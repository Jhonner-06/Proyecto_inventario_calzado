import pyodbc

def obtener_conexion():
    config = (
        "DRIVER={SQL Server};"
        "SERVER=DESKTOP-5EM5834;"
        "DATABASE=mydb;"
        "Trusted_Connection=yes;"
    )
    try:
        conn = pyodbc.connect(config)
        return conn
    except Exception as e:
        print(f"❌ Error de conexión: {e}")
        return None
    
if __name__ == "__main__":
    conexion = obtener_conexion()
    if conexion:
        print("✅ La base de la conexión funciona correctamente.")
        conexion.close()