-- CreateTable
CREATE TABLE `article` (
    `article_idx` INTEGER NOT NULL AUTO_INCREMENT,
    `title` VARCHAR(50) NULL,
    `link` TEXT NULL,
    `created_at` DATETIME(0) NULL,

    PRIMARY KEY (`article_idx`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `inductors` (
    `id` INTEGER NOT NULL AUTO_INCREMENT,
    `Manufacturer` VARCHAR(100) NULL,
    `Part_Number` VARCHAR(100) NULL,
    `Size` VARCHAR(50) NULL,
    `Inductance_nH` FLOAT NULL,
    `Tolerance_percent` FLOAT NULL,
    `Current_Rating_mA` FLOAT NULL,
    `DCR_mohm` FLOAT NULL,
    `Structure` VARCHAR(50) NULL,
    `Stock_Qty` INTEGER NULL,

    PRIMARY KEY (`id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `pcb_parts` (
    `part_id` INTEGER NOT NULL AUTO_INCREMENT,
    `part_number` VARCHAR(500) NULL,
    `category` VARCHAR(500) NULL,
    `size` VARCHAR(500) NULL,
    `received_date` DATE NULL,
    `is_humidity_sensitive` BOOLEAN NULL,
    `needs_humidity_control` BOOLEAN NULL,
    `manufacturer` VARCHAR(500) NULL,
    `quantity` INTEGER NULL,
    `min_stock` INTEGER NULL,

    PRIMARY KEY (`part_id`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- CreateTable
CREATE TABLE `user` (
    `user_idx` INTEGER NOT NULL AUTO_INCREMENT,
    `id` VARCHAR(300) NULL,
    `pw` VARCHAR(300) NULL,
    `nick` VARCHAR(50) NULL,
    `address` VARCHAR(400) NULL,
    `created_at` DATETIME(0) NULL,

    UNIQUE INDEX `id_u`(`id`),
    UNIQUE INDEX `nick_u`(`nick`),
    INDEX `id`(`id`),
    INDEX `nick`(`nick`),
    PRIMARY KEY (`user_idx`)
) DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
