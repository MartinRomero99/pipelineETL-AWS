import boto3
import pandas as pd
from io import BytesIO, StringIO

# Configuración de S3
BUCKET_NAME = 'saura-pl-s3'
RAW_PREFIX = 'raw'
PROCESSED_PREFIX = 'processed'

s3 = boto3.client('s3')


# EXTRACT: leer los CSV directamente desde S3
def extract():
    archivos = {
        'orders': 'ecommerce_orders.csv',
        'order_items': 'ecommerce_order_items.csv',
        'customers': 'ecommerce_customers.csv',
        'products': 'ecommerce_products.csv'
    }

    tablas = {}

    for nombre, archivo in archivos.items():
        key = f'{RAW_PREFIX}/{archivo}'

        response = s3.get_object(
            Bucket=BUCKET_NAME,
            Key=key
        )

        tablas[nombre] = pd.read_csv(
            BytesIO(response['Body'].read())
        )

        print(f'{archivo}: {len(tablas[nombre])} filas cargadas')

    return tablas


# EXPLORACIÓN: resumen general y valores nulos
def explore(tablas):
    for nombre, df in tablas.items():
        print(f'\n--- {nombre.upper()} ---')
        print(f'Filas: {len(df)} | Columnas: {len(df.columns)}')
        print('\nNulos por columna:')
        print(df.isnull().sum())

        print('\nPorcentaje de nulos:')
        print((df.isnull().mean() * 100).round(2))

    print('\nPrimeras filas de orders:')
    print(tablas['orders'].head())


# TRANSFORM: limpieza de órdenes
def transform_orders(df):
    print('\nLimpiando órdenes...')

    df = df.copy()
    filas_iniciales = len(df)

    # Eliminar registros sin datos esenciales
    df = df.dropna(subset=['customer_id', 'total_amount'])

    # Corregir tipos de datos
    df['order_date'] = pd.to_datetime(
        df['order_date'], errors='coerce'
    )
    df['total_amount'] = pd.to_numeric(
        df['total_amount'], errors='coerce'
    )
    df['customer_id'] = pd.to_numeric(
        df['customer_id'], errors='coerce'
    )

    # Eliminar registros que no pudieron convertirse
    df = df.dropna(
        subset=['customer_id', 'total_amount', 'order_date']
    )

    df['customer_id'] = df['customer_id'].astype('Int64')

    # Eliminar duplicados exactos y órdenes repetidas
    duplicados = df.duplicated().sum()
    print(f'Duplicados exactos encontrados: {duplicados}')

    df = df.drop_duplicates()
    df = df.sort_values('order_date')
    df = df.drop_duplicates(subset=['order_id'], keep='last')

    print(f'Filas iniciales: {filas_iniciales}')
    print(f'Filas finales: {len(df)}')
    print(f'Filas eliminadas: {filas_iniciales - len(df)}')

    return df


# TRANSFORM: análisis de ventas
def analyze_sales(df_orders, df_order_items):

    # Pregunta 1: Top 5 clientes por gasto total
    ventas_cliente = (
        df_orders.groupby('customer_id')
        .agg(
            total_gastado=('total_amount', 'sum'),
            cantidad_ordenes=('order_id', 'count')
        )
        .sort_values('total_gastado', ascending=False)
    )

    print('\nTop 5 clientes por gasto:')
    print(ventas_cliente.head(5))

    # Pregunta 2: productos más vendidos por cantidad
    items = df_order_items.copy()

    items['quantity'] = pd.to_numeric(
        items['quantity'], errors='coerce'
    )

    items = items.dropna(subset=['product_id', 'quantity'])

    productos_vendidos = (
        items.groupby('product_id')['quantity']
        .sum()
        .sort_values(ascending=False)
    )

    print('\nTop 5 productos por unidades vendidas:')
    print(productos_vendidos.head(5))

    if not productos_vendidos.empty:
        print(
            f'\nProducto más vendido: ID {productos_vendidos.idxmax()} '
            f'({productos_vendidos.max()} unidades)'
        )

    # Pregunta 3: evolución mensual de ventas
    df_orders = df_orders.copy()
    df_orders['mes'] = df_orders['order_date'].dt.to_period('M').astype(str)

    ventas_mes = (
        df_orders.groupby('mes')['total_amount']
        .sum()
        .reset_index(name='total_ventas')
    )

    print('\nVentas por mes:')
    print(ventas_mes)

    return ventas_cliente, productos_vendidos, ventas_mes


# LOAD: guardar resultados directamente en S3
def save_to_s3(df, filename, file_format):
    buffer = BytesIO() if file_format == 'parquet' else StringIO()

    if file_format == 'parquet':
        df.to_parquet(buffer, index=False, engine='pyarrow')
        content_type = 'application/octet-stream'
    else:
        df.to_csv(buffer, index=False)
        content_type = 'text/csv'

    key = f'{PROCESSED_PREFIX}/{filename}'

    s3.put_object(
        Bucket=BUCKET_NAME,
        Key=key,
        Body=buffer.getvalue(),
        ContentType=content_type
    )

    size_kb = len(buffer.getvalue()) / 1024

    print(f'Guardado: s3://{BUCKET_NAME}/{key} ({size_kb:.1f} KB)')

    return size_kb


# MAIN: ejecutar el pipeline completo
def main():
    print('Iniciando pipeline ETL...\n')

    # Extract
    tablas = extract()

    # Exploración
    explore(tablas)

    # Transform
    orders_clean = transform_orders(tablas['orders'])

    ventas_cliente, productos_vendidos, ventas_mes = analyze_sales(
        orders_clean,
        tablas['order_items']
    )

    # Load
    print('\nGuardando resultados en S3...')

    csv_size = save_to_s3(
        orders_clean, 'orders_clean.csv', 'csv'
    )

    parquet_size = save_to_s3(
        orders_clean, 'orders_clean.parquet', 'parquet'
    )

    save_to_s3(
        ventas_cliente.reset_index(),
        'ventas_por_cliente.csv',
        'csv'
    )

    save_to_s3(
        ventas_mes,
        'ventas_por_mes.csv',
        'csv'
    )

    save_to_s3(
        productos_vendidos.rename('unidades_vendidas').reset_index(),
        'productos_vendidos.csv',
        'csv'
    )

    # Comparación de tamaños
    print('\nComparación CSV vs Parquet:')
    print(f'Tamaño CSV: {csv_size:.1f} KB')
    print(f'Tamaño Parquet: {parquet_size:.1f} KB')

    if parquet_size > 0:
        print(f'Relación de tamaños: {csv_size / parquet_size:.1f}x')

    print('\nPipeline ETL finalizado correctamente.')


if __name__ == '__main__':
    main()
