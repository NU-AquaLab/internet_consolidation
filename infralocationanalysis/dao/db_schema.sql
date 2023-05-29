CREATE TABLE dns_analysis (
    id                   SERIAL PRIMARY KEY,
    country_code         VARCHAR(50) NOT NULL,
    third_party_reliance FLOAT NOT NULL,
    third_private        FLOAT NOT NULL,
    redundant            FLOAT NOT NULL,
    critically_dependant FLOAT NOT NULL,
    gen_year             FLOAT NOT NULL,
    consolidation        FLOAT NOT NULL,
    create_time          TIMESTAMP NOT NULL,
    update_time          TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX country_year_index ON dns_analysis (country_code, gen_year);

CREATE TABLE ca_analysis (
    id                   SERIAL PRIMARY KEY,
    country_code         VARCHAR(50) NOT NULL,
    ocsp                 FLOAT NOT NULL,
    https                FLOAT NOT NULL,
    third                FLOAT NOT NULL,
    critically_dependent FLOAT NOT NULL,
    most_popular_ca      VARCHAR(250) NOT NULL,
    gen_year             FLOAT NOT NULL,
    consolidation        FLOAT NOT NULL,
    create_time          TIMESTAMP NOT NULL,
    update_time          TIMESTAMP NOT NULL
);

CREATE UNIQUE INDEX ca_country_year_index ON ca_analysis (country_code, gen_year);

CREATE TABLE cdn_analysis
(
    id                   SERIAL PRIMARY KEY,
    country_code         VARCHAR(50) NOT NULL,
    third_party_reliance FLOAT       NOT NULL,
    critical_dependency  FLOAT       NOT NULL,
    redundant            FLOAT       NOT NULL,
    multiple_third_party FLOAT       NOT NULL,
    third_private        FLOAT       NOT NULL,
    gen_year             FLOAT       NOT NULL,
    consolidation        FLOAT       NOT NULL,
    create_time          TIMESTAMP   NOT NULL,
    update_time          TIMESTAMP   NOT NULL
);

CREATE UNIQUE INDEX cdn_country_year_index ON cdn_analysis (country_code, gen_year);