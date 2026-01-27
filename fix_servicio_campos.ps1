$env:PGPASSWORD = "123456"

$dbHost = "localhost"
$dbPort = "5432"
$dbName = "empresa_db"
$dbUser = "postgres"

$sql = @"
ALTER TABLE servicios
    ALTER COLUMN contador_actual TYPE INTEGER USING contador_actual::integer;

ALTER TABLE servicios
    ALTER COLUMN rango_inicio TYPE INTEGER USING rango_inicio::integer;

ALTER TABLE servicios
    ALTER COLUMN rango_fin TYPE INTEGER USING rango_fin::integer;
"@

psql -h $dbHost -p $dbPort -U $dbUser -d $dbName -c "$sql"

Write-Host "Conversión completada correctamente."

