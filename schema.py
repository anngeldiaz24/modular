instructions = [
    'SET FOREIGN_KEY_CHECKS=0;',
    'DROP TABLE IF EXISTS codigos_acceso;',
    'DROP TABLE IF EXISTS hogares;',
    'DROP TABLE IF EXISTS users;',
    'DROP TABLE IF EXISTS estados;',
    'DROP TABLE IF EXISTS eventos;',
    'DROP TABLE IF EXISTS periodos;',
    'DROP TABLE IF EXISTS registros_eventos;',
    'DROP TABLE IF EXISTS consumo_energia;',
    'DROP TABLE IF EXISTS consumo_agua;',
    'DROP TABLE IF EXISTS dispositivos;',
    'SET FOREIGN_KEY_CHECKS=1;',
    """
        -- Creación de la tabla codigos_acceso
        CREATE TABLE codigos_acceso (
            id INT(10) AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(10) NOT NULL,
            paquete VARCHAR(100) NOT NULL,
            disponible BOOLEAN
        );
    """,
    """
        -- Creación de la tabla hogares
        CREATE TABLE hogares (
            id INT(10) AUTO_INCREMENT PRIMARY KEY,
            codigo_postal VARCHAR(10) NOT NULL,
            calle VARCHAR(255) NOT NULL,
            numero_exterior VARCHAR(10) NOT NULL,
            numero_interior VARCHAR(10) NULL,
            colonia VARCHAR(255) NOT NULL,
            municipio VARCHAR(255) NOT NULL,
            estado VARCHAR(255) NOT NULL,
            informacion_adicional VARCHAR(255) NULL,
            estatus ENUM('activo', 'inactivo') NOT NULL DEFAULT 'activo'
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
            FOREIGN KEY (hogar_id) REFERENCES hogares(id) ON DELETE CASCADE
        );
    """,
    """
        -- Creación de la tabla estados
        CREATE TABLE estados (
            id INT(10) AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL
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
        -- Creación de la tabla periodos
        CREATE TABLE periodos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL,
            inicio DATE NOT NULL,
            fin DATE NOT NULL
        );
    """,
    """
        -- Creación de la tabla registros_eventos
        CREATE TABLE registros_eventos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hogar_id INT NOT NULL,
            usuario_id INT NOT NULL,
            evento_id INT NOT NULL,
            periodo_id INT NOT NULL,
            FOREIGN KEY (hogar_id) REFERENCES hogares(id),
            FOREIGN KEY (usuario_id) REFERENCES users(id),
            FOREIGN KEY (evento_id) REFERENCES eventos(id),
            FOREIGN KEY (periodo_id) REFERENCES periodos(id)
        );
    """,
    """
        -- Creación de la tabla consumo_energia
        CREATE TABLE consumo_energia (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hogar_id INT NOT NULL,
            periodo_id INT NOT NULL,
            consumo_kwh DECIMAL(10, 2) NOT NULL,
            tarifa ENUM('básico', 'intermedio-bajo', 'intermedio-alto', 'excedente') NULL,
            precio_energia DECIMAL(5, 3) NULL,
            precio_total DECIMAL(10, 2) NULL,
            FOREIGN KEY (hogar_id) REFERENCES hogares(id),
            FOREIGN KEY (periodo_id) REFERENCES periodos(id)
        );
    """,
    """
        -- Creación de la tabla consumo_agua
        CREATE TABLE consumo_agua (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hogar_id INT NOT NULL,
            periodo_id INT NOT NULL,
            consumo_litros DECIMAL(10, 2) NOT NULL,
            FOREIGN KEY (hogar_id) REFERENCES hogares(id),
            FOREIGN KEY (periodo_id) REFERENCES periodos(id)
        );
    """,
    """
        -- Creación de la tabla dispositivos
        CREATE TABLE dispositivos (
            id INT AUTO_INCREMENT PRIMARY KEY,
            hogar_id INT NOT NULL,
            user_id INT NOT NULL,
            tipo VARCHAR(255) NOT NULL,
            estado ENUM('conectado', 'desconectado') NOT NULL,
            FOREIGN KEY (hogar_id) REFERENCES hogares(id),
            FOREIGN KEY (user_id) REFERENCES users(id)
        );
    """,
]
