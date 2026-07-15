"""Script auxiliar para listar los escáneres WIA instalados."""
import scanner

devs = scanner.list_devices()
print(f"{len(devs)} dispositivo(s) WIA encontrado(s):\n")
for i, d in enumerate(devs, 1):
    print(f"  {i}. Nombre: {d['name']}")
    print(f"     Descripcion: {d['description']}")
    print(f"     ID: {d['id']}")
    print()
