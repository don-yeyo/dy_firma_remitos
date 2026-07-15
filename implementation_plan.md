# Plan de Implementación: Reglas de Negocio para Confirmación de Firmas (Operador y Distribuidor)

Este plan detalla los cambios requeridos para implementar las reglas de negocio sobre los campos `bot_confirmado_cliente` (Operador Logístico) y `bot_confirmado_distribuidor` (Distribuidor) de la tabla `remitos`. Asimismo, se define cómo consolidar las firmas de ejemplares que llegan en diferentes momentos y cómo generar el resumen final del lote procesado.

## Reglas de Negocio a Implementar

### Requerimiento de Firmas según Copias (`finne_Copias`)
- **Si `finne_Copias == 2`**:
  - Solo se espera la firma del **Distribuidor** (`bot_confirmado_distribuidor`).
  - La firma del **Operador Logístico** (`bot_confirmado_cliente`) **no se requiere**.
- **Si `finne_Copias > 2`**:
  - Se espera la firma tanto del **Operador Logístico** (`bot_confirmado_cliente`) como la del **Distribuidor** (`bot_confirmado_distribuidor`).

### Criterio de Firma de Ejemplares
- **Firma del Operador Logístico**: Se considera que firmó si el ejemplar **Duplicado** (`ocr_duplicado`) contiene al menos una firma o al menos un sello.
- **Firma del Distribuidor**:
  - Si `finne_Copias == 2`: Se considera que firmó si el ejemplar **Duplicado** (`ocr_duplicado`) contiene al menos una firma o al menos un sello.
  - Si `finne_Copias > 2`: Se considera que firmó si alguno de los ejemplares **Triplicado** (`ocr_triplicado`) o **Cuatriplicado** (`ocr_cuatriplcado`) contiene al menos una firma o al menos un sello.

---

## Cambios Propuestos

### Mapeo y Persistencia

---

#### [MODIFY] [recognition.py](file:///c:/Users/gabrielt/Documents/Proyectos/AutomatizaciónRecepcionDocumentos/dy_automatizacion_recepcion_docs/recognition.py)
- **Modificación de `_update_database_record`**:
  1. Consultar de la base de datos el registro actual coincidente por `finne_transaccionID = transaccion_id`.
  2. Leer las columnas `finne_Copias`, `ocr_original`, `ocr_duplicado`, `ocr_triplicado` y `ocr_cuatriplcado`.
  3. Consolidar la respuesta actual en el campo correspondiente (por ejemplo, si estamos procesando un Triplicado, actualizamos la columna de Triplicado conservando lo que ya hubiera en Duplicado y Original).
  4. Analizar la presencia de firmas/sellos en cada ejemplar consolidador para determinar `bot_confirmado_cliente` y `bot_confirmado_distribuidor` de acuerdo con las reglas de negocio detalladas anteriormente.
  5. Actualizar en la base de datos tanto la columna del ejemplar actual como los campos de confirmación:
     ```sql
     UPDATE remitos SET {campo_db} = %s, bot_confirmado_cliente = %s, bot_confirmado_distribuidor = %s WHERE id = %s
     ```
  6. Retornar un diccionario de estado del procesamiento de base de datos para la consolidación del reporte.
- **Modificación de `process_document`**:
  - Devolver el diccionario de estado obtenido de la persistencia de base de datos en su retorno.
- **Modificación de `process_all_scans`**:
  - Mantener un registro de los resultados individuales procesados.
  - Al final de la ejecución de todas las imágenes, generar un contador incremental de lotes almacenado localmente en `parsed_documents/lote_counter.txt`.
  - Imprimir en consola el reporte consolidado `"RESUMEN DE DETECCION DE FIRMAS"` con la fecha actual y el lote correspondiente.

---

## Plan de Verificación

### Pruebas Unitarias de Reglas de Negocio en Scratch
- Actualizaremos `scratch/test_db_integration.py` para incluir pruebas unitarias específicas de la lógica de evaluación de firmas (comprobando casos con copias = 2 y copias > 2 bajo diferentes combinaciones de firmas y sellos).

### Verificación de Sintaxis
- Ejecutar compilación de sintaxis Python para asegurar la consistencia del código modificado.
