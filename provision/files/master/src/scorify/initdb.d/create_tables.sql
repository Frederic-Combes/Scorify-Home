CREATE TABLE job_info (
    `hash` VARCHAR(64),
    `name` VARCHAR(64),
    `uid` VARCHAR(64) NOT NULL,
    `order` INT,
    PRIMARY KEY(uid)
);

CREATE TABLE job_status (
    `uid` VARCHAR(64) NOT NULL,
    `creation_time` TIMESTAMP,
    `update_time` TIMESTAMP,
    `status` VARCHAR(64),
    `progress` INT,
    `total` INT,
    PRIMARY KEY(uid)
);
