# ETL E-commerce con Python y AWS S3

Pipeline ETL desarrollado con Python para extraer, limpiar, transformar y analizar datos de e-commerce, utilizando Amazon S3 como almacenamiento de datos.

El proyecto parte de un procesamiento local con archivos CSV y evoluciona hacia una solución que permite leer los datos originales desde S3 y almacenar los resultados procesados directamente en la nube.

## Objetivos

- Integrar Python con Amazon S3 mediante Boto3.
- Automatizar la extracción de archivos CSV desde un bucket.
- Limpiar y transformar datos utilizando Pandas.
- Generar métricas de ventas para el análisis comercial.
- Almacenar los resultados en formatos CSV y Parquet.
- Comparar el tamaño de almacenamiento entre ambos formatos.

## Tecnologías utilizadas

- **Python:** lenguaje de programación.
- **Pandas:** manipulación, limpieza y análisis de datos.
- **Boto3:** integración con servicios de AWS.
- **Amazon S3:** almacenamiento de datos en la nube.
- **PyArrow:** soporte para trabajar con archivos Parquet.

## Arquitectura del proyecto

El bucket de Amazon S3 se organiza en dos carpetas principales:

```text
saura-pl-s3/
│
├── raw/
│   ├── ecommerce_orders.csv
│   ├── ecommerce_order_items.csv
│   ├── ecommerce_customers.csv
│   └── ecommerce_products.csv
│
└── processed/
    ├── orders_clean.csv
    ├── orders_clean.parquet
    ├── ventas_por_cliente.csv
    ├── ventas_por_mes.csv
    └── productos_vendidos.csv
```

- **Raw:** contiene los archivos originales utilizados como fuente de datos.
- **Processed:** almacena los resultados generados por el pipeline ETL.

## Proceso ETL

### 1. Extract

Se utiliza Boto3 para conectarse a Amazon S3 y obtener los archivos CSV almacenados en la carpeta `raw/`.

Los archivos se leen directamente desde memoria utilizando `BytesIO` y Pandas, sin necesidad de descargarlos localmente.

Tablas utilizadas:
- Orders
- Order Items
- Customers
- Products

### 2. Transform

Se realizan tareas de exploración, limpieza y transformación de datos.

**Limpieza de órdenes:**
- Identificación de valores nulos.
- Eliminación de registros sin datos esenciales.
- Corrección de tipos de datos.
- Conversión de fechas e importes.
- Eliminación de duplicados exactos.
- Eliminación de órdenes repetidas, conservando el registro más reciente.

**Análisis de datos:**

Se desarrollan tres análisis principales:

- **Ventas por cliente:** cálculo del gasto total y cantidad de órdenes por cliente, identificando los cinco clientes con mayor gasto.
- **Productos más vendidos:** identificación de los productos con mayor cantidad de unidades vendidas.
- **Evolución mensual:** agrupación de las ventas por mes para analizar su comportamiento a lo largo del tiempo.

### 3. Load

Los resultados se almacenan directamente en la carpeta `processed/` del bucket S3.

Archivos generados:

| Archivo | Descripción |
|---|---|
| `orders_clean.csv` | Órdenes limpias en formato CSV. |
| `orders_clean.parquet` | Órdenes limpias en formato Parquet. |
| `ventas_por_cliente.csv` | Métricas de ventas agrupadas por cliente. |
| `ventas_por_mes.csv` | Evolución mensual de las ventas. |
| `productos_vendidos.csv` | Cantidad de unidades vendidas por producto. |

También se realiza una comparación entre el tamaño de los archivos CSV y Parquet para observar las diferencias de almacenamiento.

## Estructura del código

El script `scriptETL_s3.py` organiza el procesamiento mediante las siguientes funciones:

| Función | Responsabilidad |
|---|---|
| `extract()` | Obtiene los archivos desde S3. |
| `explore()` | Explora las tablas y analiza valores nulos. |
| `transform_orders()` | Limpia y transforma las órdenes. |
| `analyze_sales()` | Genera las métricas y análisis comerciales. |
| `save_to_s3()` | Guarda los resultados en el bucket. |
| `main()` | Coordina la ejecución completa del pipeline. |

## Instalación y configuración

### Requisitos previos

- Python 3.11 o superior.
- Una cuenta de AWS.
- Un bucket de Amazon S3.
- AWS CLI instalado y configurado.
- Permisos IAM para leer los archivos de `raw/` y escribir resultados en `processed/`.

### 1. Clonar el repositorio

```bash
git clone https://github.com/TU-USUARIO/etl-ecommerce-aws-s3.git
cd etl-ecommerce-aws-s3
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar AWS CLI

Configurar las credenciales mediante:

```bash
aws configure
```

Verificar la identidad configurada:

```bash
aws sts get-caller-identity
```

No incluir credenciales de AWS directamente en el código ni en el repositorio.

### 4. Configurar el bucket

En `scriptETL_s3.py`, verificar que el nombre del bucket coincida con el propio:

```python
BUCKET_NAME = 'saura-pl-s3'
```

Los archivos CSV deben estar cargados previamente en la carpeta `raw/`.

### 5. Ejecutar el pipeline

```bash
python scriptETL_s3.py
```

Al finalizar, los archivos procesados estarán disponibles en la carpeta `processed/` del bucket S3.

## Capturas de pantalla

Las siguientes capturas muestran la organización de los datos en S3 y la ejecución del pipeline.

### Organización del bucket S3

![Bucket S3](screenshots/s3-raw.png)

### Resultados procesados

![Processed](screenshots/s3-processed.png)

### Ejecución del pipeline

![Ejecución ETL](screenshots/pipeline-execution.png)

## Conclusiones

Este proyecto permitió profundizar en la construcción de pipelines ETL con Python e incorporar servicios de AWS para trabajar con datos almacenados en la nube.

También permitió poner en práctica conceptos de limpieza, transformación, análisis y almacenamiento de datos, utilizando formatos como CSV y Parquet.

El desarrollo forma parte de mi proceso de aprendizaje y especialización en Ingeniería de Datos.