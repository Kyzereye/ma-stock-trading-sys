
-- Drop tables if they exist (in reverse order due to foreign key constraints)
DROP TABLE IF EXISTS user_preferences;
DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS technical_indicators;
DROP TABLE IF EXISTS daily_stock_data;
DROP TABLE IF EXISTS stock_symbols;

-- Create users table
CREATE TABLE IF NOT EXISTS users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password_hash VARCHAR(255) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP NULL,
    is_active BOOLEAN DEFAULT TRUE,
    email_verified BOOLEAN DEFAULT FALSE,
    verification_token VARCHAR(255) NULL,
    verification_token_expires TIMESTAMP NULL,
    INDEX idx_email (email),
    INDEX idx_active (is_active),
    INDEX idx_verification_token (verification_token)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- Create user_preferences table
CREATE TABLE IF NOT EXISTS user_preferences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    name VARCHAR(100) NOT NULL,
    default_days INT DEFAULT 365,
    default_atr_period INT DEFAULT 14,
    default_atr_multiplier DECIMAL(3,1) DEFAULT 2.0,
    default_ma_type VARCHAR(10) DEFAULT 'ema',
    default_initial_capital DECIMAL(15,2) DEFAULT 100000.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_user_id (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;





-- Table 1: Stock Symbols/Tickers
CREATE TABLE IF NOT EXISTS stock_symbols (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol VARCHAR(10) UNIQUE NOT NULL,
    company_name VARCHAR(255),
    INDEX idx_symbol (symbol)
);

-- Table 2: Daily Stock Data (OHLCV)
CREATE TABLE IF NOT EXISTS daily_stock_data (
    id INT AUTO_INCREMENT PRIMARY KEY,
    symbol_id INT NOT NULL,
    date DATE NOT NULL,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (symbol_id) REFERENCES stock_symbols(id) ON DELETE CASCADE,
    UNIQUE KEY unique_symbol_date (symbol_id, date),
    INDEX idx_symbol_id (symbol_id),
    INDEX idx_date (date),
    INDEX idx_symbol_date (symbol_id, date)
);


-- Insert some sample stock symbols (optional - you can populate this from your stock_symbols.txt)
INSERT IGNORE INTO stock_symbols (symbol, company_name) VALUES

('DOMO', 'Domo Inc.'),
('ACHR', 'Archer Aviation'),
('ADPT', 'Adaptive Biotechnologies Corporation'),
('ADT', 'ADT Inc.'),
('AMPX', 'Amprius Technologies Inc.'),
('APLD', 'Applied Digital Corp.'),
('ARKX', 'ARK Space Exploration & Innovation ETF'),
('AMRC', 'Ameresco Inc.'),
('ARMN', 'Aris Mining Corp.'),
('ASPI', 'ASP Isotopes Inc.'),
('BKKT', 'Bakkt Holdings Inc.'),
('BKSY', 'BlackSky Technology Inc.'),
('BTM', 'Bitcoin Trust'),
('CORZ', 'Core Scientific Inc.'),
('CPS', 'Copper-Standard Holdings Inc.'),
('CURI', 'CuriosityStream Inc.'),
('ETHD', 'ProShares UltraShort Ether ETF'),
('EOSE', 'Eos Energy Enterprises Inc.'),
('EVLV', 'Evolv Technologies Holdings Inc.'),
('FCEL', 'FuelCell Energy Inc.'),
('FSTO', 'Fastly Inc.'),
('FSTR', 'L.B. Foster Company')
('FTEK', 'Fuel Tech Inc.'),
('GRNT', 'Granite Ridge Resources Inc.'),
('GRND', 'Grindr Ltd.'),
('GPRK', 'GeoPark Ltd.'),
('HDSN', 'Hudson Technologies Inc.'),
('HTZ', 'Hertz Global Holdings Inc.'),
('HUSA', 'Houston American Energy Corp.'),
('HUT', 'Hut 8 Corp.'),
('IREN', 'IREN Limited.'),
('JBI', 'Janus International Group'),
('JOBY', 'Joby Aviation Inc.'),
('KODK', 'Eastman Kodak Co.'),
('KOPN', 'Kopin Corp.'),
('LTBR', 'Lightbridge Corp.'),
('LYFT', 'Lyft Inc.'),
('MAPS', 'WM Technology, Inc'),
('MARA', 'MARA Holdings, Inc'),
('METC', 'Ramaco Resources Inc.'),
('MQ', 'Marqeta Inc.'),
('NEXT', 'NextDecade Corp.'),
('NG', 'Novagold Resources Inc.'),
('NPKI', 'NPK International Inc.'),
('OM', 'Outset Medical Inc.'),
('PBYI', 'Puma Biotechnology Inc.'),
('PDYN', 'Palladyne AI Corp.'),
('PGEN', 'Precigen Inc.'),
('PINC', 'Premier, Inc'),
('PONY', 'Pony AI Inc.'),
('PPTA', 'Perpetua Resources Corp.'),
('PRCH', 'Porch Group Inc.'),
('ROW', 'Redwire Corp.'),
('RXST', 'RxSight Inc.'),
('RUN', 'Sunrun Inc.'),
('QBTS', 'D-Wave Quantum Inc.'),
('QS', 'QuantumScape Corp.'),
('QUBT', 'Quantum Computing Inc.'),
('RGTI', 'Rigetti Computing Inc.'),
('SATL', 'Satellogic Inc.'),
('SERV', 'Serve Robotics Inc.'),
('SHLS', 'Shoals Technologies Group, Inc.'),
('SLDB', 'GraniteShares 2x Long SMCI Daily ETF'),
('SMCL', 'Super Micro Computer Inc.'),
('SMST', 'Defiance Daily Target 2X short MSTR ETF'),
('SNDL', 'SNDL Inc.'),
('SOFI', 'SoFi Technologies Inc.'),
('SRFM', 'Surf Air Mobility Inc.'),
('SSRM', 'SSR Mining Inc.'),
('STNE', 'StoneCo Ltd.'),
('TSSI', 'TSS Inc'),
('AEHR', 'Aehr Test Systems'),
('UEC', 'Uranium Energy Corp.'),
('UUUU', 'Energy Fuels Inc.'),
('YEXT', 'Yext Inc.'),
('UMAC', 'Unusual Machines Inc.'),
('USAR', 'USA Rare Earth Inc.'),
('VG', 'Virgin Global Inc.'),
('VSCO', 'Victorias Secret & Co.'),
('VTLE', 'Vital Energy Inc.'),
('FLO', 'Flower Foods Corp.'),
('AA', 'Alcoa Corp.'),
('FIVN', 'Five9 Inc.'),
('TTC', 'Toro Co.'),
('URBN', 'Urban Outfitters Inc.'),
('ALGT', 'Allegiant Travel Co.'),
('ACLS', 'Axcelis Technologies Inc.'),
('UFPI', 'UFP Industries Inc.'),
('SHAK', 'Shake Shack Inc.'),
('SATS', 'EchoStar Corp.'),
('BBIO', 'BridgeBio Pharma Inc.'),
('KTOS', 'Kratos Defense & Security Solutions Inc.'),
('BLKB', 'Blackbaud Inc.'),
('NXT', 'Nextracker Inc.'),
('RMBS', 'Rambus Inc.'),
('HIMS', 'Hims & Hers Health Inc.'),
('DAN', 'Dana Inc.'),
('ENPH', 'Enphase Energy Inc.'),
('MGNI', 'Magnite Inc.'),
('SOC', 'Sable Offshore Corp.'),
('VSAT', 'Viasat Inc.'),
('GPRE', 'Green Plains Inc.'),
('KSS', 'Kohls Corp.'),
('NN', 'NextNav Inc.'),
('PCT', 'PureCycle Technologies Inc.'),
('ROOX', 'Roblox Corp.'),
('STEM', 'Stem Inc.'),
('TSLL', 'Direxion Daily TSLA Bull 1.5X Shares');




;

INSERT IGNORE INTO stock_symbols (symbol, company_name) VALUES
('A', 'Agilent Technologies Inc.'),
('MMM', '3M Co.'),
('GOOGL', 'Alphabet Inc. Class A'),
('TSLA', 'Tesla Inc.'),
('AAPL', 'Apple Inc.'),
('AMZN', 'Amazon.com, Inc.'),
('AXP', 'American Express Co.'),
('AMGN', 'Amgen Inc.'),
('BA', 'The Boeing Co.'),
('CAT', 'Caterpillar Inc.'),
('CVX', 'Chevron Corp.'),
('CSCO', 'Cisco Systems, Inc.'),
('KO', 'The Coca-Cola Co.'),
('CRM', 'Salesforce, Inc.'),
('DIS', 'The Walt Disney Co.'),
('GS', 'The Goldman Sachs Group, Inc.'),
('HD', 'The Home Depot, Inc.'),
('HON', 'Honeywell International Inc.'),
('IBM', 'International Business Machines Corp.'),
('JNJ', 'Johnson & Johnson'),
('JPM', 'JPMorgan Chase & Co.'),
('MCD', 'McDonald''s Corp.'),
('MRK', 'Merck & Co., Inc.'),
('MSFT', 'Microsoft Corp.'),
('NKE', 'Nike, Inc.'),
('NVDA', 'Nvidia Corporation'),
('PG', 'The Procter & Gamble Co.'),
('SHW', 'The Sherwin-Williams Company'),
('TRV', 'The Travelers Companies, Inc.'),
('UNH', 'UnitedHealth Group Inc.'),
('VZ', 'Verizon Communications Inc.'),
('V', 'Visa Inc.'),
('WMT', 'Walmart Inc.');