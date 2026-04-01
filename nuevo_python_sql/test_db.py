import pyodbc

# Configuración con los datos de tu servidor
# 'Trusted_Connection=yes' usa tu sesión de Windows actual (sin contraseña)
config = (
    "DRIVER={SQL Server};"
    "SERVER=DESKTOP-5EM5834;"
    "DATABASE=mydb1;"
    "Trusted_Connection=yes;"
)

try:
    # Intentar establecer la conexión
    conn = pyodbc.connect(config)
    print("✅ ¡Conexión exitosa desde Python!")



except Exception as e:
    print(f"❌ Error al intentar conectar: {e}")