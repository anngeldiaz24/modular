instructions = [
    'SET FOREIGN_KEY_CHECKS=0;',
    'DROP TABLE IF EXISTS users;',
    'DROP TABLE IF EXISTS hogares;',
    'DROP TABLE IF EXISTS codigos_acceso;',
    'DROP TABLE IF EXISTS eventos;',
    'DROP TABLE IF EXISTS registros_eventos;',
    'DROP TABLE IF EXISTS alertas;',
    'DROP TABLE IF EXISTS estadisticas;',
    'SET FOREIGN_KEY_CHECKS=1;',
    """
        -- Creación de la tabla codigos_acceso
        CREATE TABLE codigos_acceso (
            id INT(10) AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(10) NOT NULL,
            disponible BOOLEAN
        );
    """,
    """
        -- Creación de la tabla hogares
        CREATE TABLE hogares (
            id INT(10) AUTO_INCREMENT PRIMARY KEY,
            direccion VARCHAR(255) NOT NULL,
            paquete ENUM('basico', 'premium', 'deluxe') NOT NULL
        );
    """,
    """
        -- Creación de la tabla users
        CREATE TABLE users (
            id INT(10) AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            apellidos VARCHAR(255) NOT NULL,
            email VARCHAR(255) NOT NULL,
            password VARCHAR(255) NOT NULL,
            telefono VARCHAR(13) NOT NULL,
            rol VARCHAR(255) NOT NULL,
            codigo_acceso INT(10),
            acepto_terminos BOOLEAN NOT NULL DEFAULT 0,
            hogar_id INT(10),
            FOREIGN KEY (codigo_acceso) REFERENCES codigos_acceso(id),
            FOREIGN KEY (hogar_id) REFERENCES hogares(id)
        );
    """,
    """
        -- Creación de la tabla eventos
        CREATE TABLE eventos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL
        );
    """,
    """
        -- Insertar eventos predefinidos
        INSERT INTO eventos (nombre) VALUES
        ('activacion_alarma'),
        ('desactivacion_alarma'),
        ('encendido_luces'),
        ('apagado_luces'),
        ('bloqueo_puerta'),
        ('desbloqueo_puerta'),
        ('monitoreo_camara'),
        ('alerta'),
        ('otro');
    """,
    """
        -- Creación de la tabla registros_eventos
        CREATE TABLE registros_eventos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hogar_id INT NOT NULL,
            evento_id INT NOT NULL,
            timestamp DATETIME NOT NULL,
            detalles TEXT,
            FOREIGN KEY (hogar_id) REFERENCES hogares(id),
            FOREIGN KEY (evento_id) REFERENCES eventos(id)
        );
    """,
    """
        -- Creación de la tabla alertas
        CREATE TABLE alertas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hogar_id INT NOT NULL,
            tipo_alerta ENUM('sospechosa', 'no_sospechosa') NOT NULL,
            timestamp DATETIME NOT NULL,
            respuesta_tiempo INT,
            FOREIGN KEY (hogar_id) REFERENCES hogares(id)
        );
    """,
    """
        -- Creación de la tabla estadisticas
        CREATE TABLE estadisticas (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hogar_id INT NOT NULL,
            evento_id INT NOT NULL,
            valor INT NOT NULL,
            periodo DATE NOT NULL,
            FOREIGN KEY (hogar_id) REFERENCES hogares(id),
            FOREIGN KEY (evento_id) REFERENCES eventos(id)
        );
    """,
    """
        -- Insertar algunos codigos de acceso
        INSERT INTO codigos_acceso (id, codigo, disponible) VALUES
        (1, '012', 0),
        (2, '345', 1),
        (3, '678', 2);
    """,
    """
        -- Insertar algunos hogares
        INSERT INTO hogares (direccion, paquete) VALUES
        ('123 Calle Principal', 'basico'),
        ('456 Calle Secundaria', 'premium'),
        ('789 Calle Terciaria', 'deluxe');
    """,
    """
        -- Insertar algunos usuarios
        INSERT INTO users (nombre, apellidos, email, password, telefono, rol, codigo_acceso, hogar_id, acepto_terminos) VALUES
        ('Juan', 'Perez', 'juan.perez@example.com', 'password', '1234567890', 'admin', 1, 1, 1),
        ('Ana', 'Gomez', 'ana.gomez@example.com', 'password', '0987654321', 'user', 2, 2, 1),
        ('Carlos', 'Lopez', 'carlos.lopez@example.com', 'password', '1122334455', 'user', 3, 3, 1);
    """,
    """
        -- Insertar algunos registros de eventos
        INSERT INTO registros_eventos (hogar_id, evento_id, timestamp, detalles) VALUES
        (1, 1, '2024-06-28 12:00:00', 'Activación de la alarma'),
        (1, 3, '2024-06-28 12:10:00', 'Encendido de las luces'),
        (2, 2, '2024-06-28 12:20:00', 'Desactivación de la alarma'),
        (3, 4, '2024-06-28 12:30:00', 'Apagado de las luces');
    """,
    """
        -- Insertar algunas alertas
        INSERT INTO alertas (hogar_id, tipo_alerta, timestamp, respuesta_tiempo) VALUES
        (1, 'sospechosa', '2024-06-28 13:00:00', 5),
        (2, 'no_sospechosa', '2024-06-28 13:10:00', 3),
        (3, 'sospechosa', '2024-06-28 13:20:00', 7);
    """,
    """
        -- Insertar algunas estadísticas
        INSERT INTO estadisticas (hogar_id, evento_id, valor, periodo) VALUES
        (1, 1, 5, '2024-06-28'),
        (1, 3, 10, '2024-06-28'),
        (2, 2, 3, '2024-06-28'),
        (3, 4, 7, '2024-06-28');
    """
]
