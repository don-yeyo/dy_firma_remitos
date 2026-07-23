#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Importador de Remitos Legacy (AppSheet / Google Sheets Excel)
Don Yeyo S.A. - Sistema de Automatización de Firma de Remitos

Uso en terminal:
  python tools/importador_legacy/importar.py
  python tools/importador_legacy/importar.py --desde 2025-01-01
"""

import os
import sys
import glob
import shutil
import argparse
try:
    import openpyxl
except ImportError:
    print("[INFO] Instalando librería 'openpyxl' necesaria para procesar archivos Excel...")
    import subprocess
    try:
        subprocess.check_call(["uv", "pip", "install", "openpyxl"])
    except Exception:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    import openpyxl
import pymysql
from dotenv import load_dotenv

# Cargar variables de entorno buscando en server/.env o .env
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, "..", ".."))

env_paths = [
    os.path.join(project_root, "server", ".env"),
    os.path.join(project_root, ".env"),
    os.path.join(script_dir, ".env")
]

for ep in env_paths:
    if os.path.exists(ep):
        load_dotenv(ep)
        break

# Conexión a Base de Datos MySQL
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "3306"))
DB_NAME = os.getenv("DB_NAME", "Firma_de_remitos")
DB_USER = os.getenv("DB_USER", "DBAdmin_Firma_de_Remitos")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")


def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Importador de remitos históricos desde archivos Excel (.xlsx) de AppSheet/Google Sheets."
    )
    parser.add_argument(
        "--desde", "-d",
        type=str,
        default=None,
        help="Fecha inicial para importar en formato YYYY-MM-DD (ej: --desde 2025-01-01). Si se omite, importa todo."
    )
    parser.add_argument(
        "--pendientes-dir",
        type=str,
        default=os.path.join(script_dir, "pendientes"),
        help="Directorio donde se encuentran los archivos .xlsx a importar."
    )
    parser.add_argument(
        "--importados-dir",
        type=str,
        default=os.path.join(script_dir, "importados"),
        help="Directorio donde se moverán los archivos .xlsx procesados."
    )
    return parser.parse_args()


def clean_int(val, default=None):
    if val is None:
        return default
    try:
        val_str = str(val).split('.')[0].strip()
        return int(val_str) if val_str else default
    except (ValueError, TypeError):
        return default


def clean_float(val, default=0.0):
    if val is None:
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def clean_str(val, max_len=None):
    if val is None:
        return None
    s = str(val).strip()
    if not s:
        return None
    if max_len and len(s) > max_len:
        s = s[:max_len]
    return s


def clean_bool(val):
    if val is None:
        return 0
    if isinstance(val, bool):
        return 1 if val else 0
    s = str(val).strip().upper()
    if s in ["1", "TRUE", "SI", "YES", "S"]:
        return 1
    return 0


def clean_date(val):
    if val is None:
        return None
    if isinstance(val, (datetime, date)):
        return val.strftime("%Y-%m-%d") if isinstance(val, datetime) else val.isoformat()
    s = str(val).strip()
    if not s or s.upper() in ["NONE", "NULL", "NAN"]:
        return None
    # Probar diferentes formatos comunes
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y"):
        try:
            dt = datetime.strptime(s.split('.')[0], fmt)
            return dt.strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def connect_db():
    try:
        conn = pymysql.connect(
            host=DB_HOST,
            port=DB_PORT,
            user=DB_USER,
            password=DB_PASSWORD,
            database=DB_NAME,
            autocommit=False,
            charset='utf8mb4'
        )
        return conn
    except Exception as e:
        print(f"[ERROR] No se pudo conectar a la base de datos MySQL ({DB_HOST}:{DB_PORT}/{DB_NAME}): {e}")
        sys.exit(1)


def get_existing_records(conn):
    """Carga los IDs de transacciones existentes en un diccionario local para optimización masiva."""
    print("[INFO] Cargando registro de transacciones existentes de la Base de Datos...")
    records = {}
    with conn.cursor() as cursor:
        sql = "SELECT finne_transaccionID, id, bot_confirmado_cliente, bot_confirmado_distribuidor FROM remitos WHERE finne_transaccionID IS NOT NULL"
        cursor.execute(sql)
        for row in cursor.fetchall():
            tx_id, db_id, bot_cli, bot_dist = row
            records[tx_id] = {
                'id': db_id,
                'bot_cli': bot_cli or 0,
                'bot_dist': bot_dist or 0
            }
    print(f"[OK] {len(records):,} transacciones cargadas en memoria.")
    return records


def process_excel_file(file_path, conn, existing_db_records, fecha_desde=None):
    filename = os.path.basename(file_path)
    print(f"\n====================================================================")
    print(f"  PROCESANDO ARCHIVO LEGACY: {filename}")
    print(f"====================================================================")
    
    try:
        wb = openpyxl.load_workbook(file_path, data_only=True)
    except Exception as e:
        print(f"[ERROR] No se pudo abrir el archivo Excel '{filename}': {e}")
        return False, 0, 0, 0, 0

    sheet = wb.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        print(f"[AVISO] El archivo '{filename}' esta vacio.")
        return True, 0, 0, 0, 0

    headers = [clean_str(h) for h in rows[0]]
    total_excel_rows = len(rows) - 1
    print(f"[INFO] Total de registros encontrados en la planilla: {total_excel_rows:,}")
    if fecha_desde:
        print(f"[INFO] Filtro activado: Importar registros con fecha >= {fecha_desde.strftime('%Y-%m-%d')}")

    inserts_batch = []
    updates_batch = []
    count_inserted = 0
    count_updated = 0
    count_skipped_date = 0
    count_skipped_invalid = 0

    for idx, r in enumerate(rows[1:], start=2):
        row_dict = dict(zip(headers, r))
        
        raw_tx_id = row_dict.get('TransaccionID')
        tx_id = clean_int(raw_tx_id)
        if not tx_id:
            count_skipped_invalid += 1
            continue

        raw_fecha = row_dict.get('Fecha')
        fecha_str = clean_date(raw_fecha)
        
        # Filtro opcional por fecha
        if fecha_desde and fecha_str:
            try:
                row_date = datetime.strptime(fecha_str, "%Y-%m-%d").date()
                if row_date < fecha_desde:
                    count_skipped_date += 1
                    continue
            except ValueError:
                pass

        cliente = clean_str(row_dict.get('Cliente'), max_len=100)
        total = clean_float(row_dict.get('Total'), default=0.0)
        comprobante = clean_str(row_dict.get('Comprobante'), max_len=30)
        doc_nro_int = clean_str(row_dict.get('Doc.Nro.Interno'), max_len=100)
        firma_cli = clean_bool(row_dict.get('Firma Cliente'))
        firma_dist = clean_bool(row_dict.get('Firma Distribuidor'))
        descripcion = clean_str(row_dict.get('Descripcion'), max_len=255)
        reclamado = clean_bool(row_dict.get('Reclamado'))
        fecha_ultimo_rec = clean_date(row_dict.get('Fecha Ultimo reclamo'))
        cod_cliente = clean_int(row_dict.get('CodigoCliente'))
        copias = clean_int(row_dict.get('Cantidad de Copias'), default=2)

        if tx_id in existing_db_records:
            # UPDATE: Preservar firmas confirmadas del sistema moderno si la BD ya las tiene registradas
            existing_rec = existing_db_records[tx_id]
            final_firma_cli = 1 if (existing_rec['bot_cli'] == 1 or firma_cli == 1) else 0
            final_firma_dist = 1 if (existing_rec['bot_dist'] == 1 or firma_dist == 1) else 0

            updates_batch.append((
                copias,
                fecha_str,
                cod_cliente,
                cliente,
                total,
                comprobante,
                reclamado,
                fecha_ultimo_rec,
                doc_nro_int,
                descripcion,
                final_firma_cli,
                final_firma_dist,
                tx_id
            ))
            count_updated += 1
        else:
            # INSERT
            inserts_batch.append((
                tx_id,
                copias,
                fecha_str,
                cod_cliente,
                cliente,
                total,
                comprobante,
                reclamado,
                fecha_ultimo_rec,
                doc_nro_int,
                descripcion,
                firma_cli,
                firma_dist
            ))
            existing_db_records[tx_id] = {
                'id': None,
                'bot_cli': firma_cli,
                'bot_dist': firma_dist
            }
            count_inserted += 1

    # Ejecutar Batch SQL de Inserts y Updates para alta velocidad
    BATCH_SIZE = 1000
    with conn.cursor() as cursor:
        if inserts_batch:
            sql_insert = """
                INSERT INTO remitos (
                    finne_transaccionID, finne_Copias, finne_Fecha, finne_CodigoCliente,
                    finne_Cliente, finne_importe_total, finne_Comprobante, finne_Reclamado,
                    finne_FechaUltimoReclamo, finne_DocNroInterno, finne_Descripcion,
                    bot_confirmado_cliente, bot_confirmado_distribuidor
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            for i in range(0, len(inserts_batch), BATCH_SIZE):
                chunk = inserts_batch[i:i + BATCH_SIZE]
                cursor.executemany(sql_insert, chunk)
                conn.commit()

        if updates_batch:
            sql_update = """
                UPDATE remitos SET
                    finne_Copias = %s,
                    finne_Fecha = %s,
                    finne_CodigoCliente = %s,
                    finne_Cliente = %s,
                    finne_importe_total = %s,
                    finne_Comprobante = %s,
                    finne_Reclamado = %s,
                    finne_FechaUltimoReclamo = %s,
                    finne_DocNroInterno = %s,
                    finne_Descripcion = %s,
                    bot_confirmado_cliente = %s,
                    bot_confirmado_distribuidor = %s
                WHERE finne_transaccionID = %s
            """
            for i in range(0, len(updates_batch), BATCH_SIZE):
                chunk = updates_batch[i:i + BATCH_SIZE]
                cursor.executemany(sql_update, chunk)
                conn.commit()

    print("\n====================================================================")
    print(f"  RESUMEN DE IMPORTACION LEGACY: {filename}")
    print("====================================================================")
    print(f"  Registros leidos en Excel: {total_excel_rows:,}")
    print(f"  Nuevos insertados:        {count_inserted:,}")
    print(f"  Existentes actualizados:  {count_updated:,}")
    print(f"  Omitidos por fecha:       {count_skipped_date:,}")
    print(f"  Omitidos por ID invalido: {count_skipped_invalid:,}")
    print("====================================================================\n")

    return True, count_inserted, count_updated, count_skipped_date, count_skipped_invalid


def main():
    args = parse_arguments()

    pendientes_dir = os.path.abspath(args.pendientes_dir)
    importados_dir = os.path.abspath(args.importados_dir)

    os.makedirs(pendientes_dir, exist_ok=True)
    os.makedirs(importados_dir, exist_ok=True)

    fecha_desde = None
    if args.desde:
        try:
            fecha_desde = datetime.strptime(args.desde, "%Y-%m-%d").date()
        except ValueError:
            print(f"[ERROR] Formato de fecha invalido '--desde {args.desde}'. Usar YYYY-MM-DD.")
            sys.exit(1)

    xlsx_files = glob.glob(os.path.join(pendientes_dir, "*.xlsx"))
    if not xlsx_files:
        print(f"[INFO] No se encontraron archivos .xlsx para importar en:")
        print(f"       {pendientes_dir}")
        print("Coloca el archivo Excel en esa carpeta y vuelve a ejecutar este comando.")
        return

    conn = connect_db()
    existing_db_records = get_existing_records(conn)

    total_inserted = 0
    total_updated = 0
    total_skipped_date = 0
    total_skipped_invalid = 0

    for file_path in xlsx_files:
        filename = os.path.basename(file_path)
        ok, ins, upd, sk_d, sk_i = process_excel_file(file_path, conn, existing_db_records, fecha_desde)
        if ok:
            total_inserted += ins
            total_updated += upd
            total_skipped_date += sk_d
            total_skipped_invalid += sk_i

            # Mover archivo procesado a importados/
            dest_path = os.path.join(importados_dir, filename)
            if os.path.exists(dest_path):
                # Generar sufijo único si ya existe
                base_name, ext = os.path.splitext(filename)
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                dest_path = os.path.join(importados_dir, f"{base_name}_{timestamp}{ext}")

            shutil.move(file_path, dest_path)
            print(f"[OK] Archivo movido exitosamente a: {dest_path}")

    conn.close()

    print("\n====================================================================")
    print("  [PROCESO GLOBAL FINALIZADO CON EXITO]")
    print("====================================================================")
    print(f"  Archivos procesados:     {len(xlsx_files):,}")
    print(f"  Total nuevos insertados: {total_inserted:,}")
    print(f"  Total actualizados:      {total_updated:,}")
    print(f"  Total omitidos:          {total_skipped_date + total_skipped_invalid:,}")
    print("====================================================================\n")


if __name__ == "__main__":
    main()
