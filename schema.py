instructions = [
    'SET FOREIGN_KEY_CHECKS=0;',
    'DROP TABLE IF EXISTS user;',
    'SET FOREIGN_KEY_CHECKS=1;',
    """
        -- Creación de la tabla codigos_acceso
        CREATE TABLE codigos_acceso (
            id INT(10) AUTO_INCREMENT PRIMARY KEY,
            codigo VARCHAR(10) NOT NULL,
            paquete ENUM('basico', 'premium', 'deluxe') NOT NULL,
            disponible BOOLEAN
        );
        
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
        
        -- Creación de la tabla estados
        CREATE TABLE estados (
            id INT(10) AUTO_INCREMENT PRIMARY KEY,
            nombre VARCHAR(255) NOT NULL      
        );
    """
]
