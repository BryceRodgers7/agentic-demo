INSERT INTO agent_shipping_rates (carrier, service_type, zip_code, base_rate, per_lb_rate, estimated_days)
VALUES
-- UPS Ground Services
('UPS','Ground','80202',8.99,1.25,4),
('UPS','Ground','95112',9.49,1.30,5),
('UPS','Ground','90028',9.29,1.30,5),
('UPS','Ground','94103',9.49,1.35,5),
('UPS','Ground','02108',10.49,1.40,5),
('UPS','Ground','53703',8.99,1.25,4),
('UPS','Ground','98101',9.99,1.35,5),
('UPS','Ground','78701',8.99,1.25,4),
('UPS','Ground','33101',10.99,1.45,6),
('UPS','Ground','80302',8.99,1.25,4),
('UPS','Ground','92618',9.29,1.30,5),
('UPS','Ground','60601',9.49,1.30,5),
('UPS','Ground','94538',9.49,1.30,5),
('UPS','Ground','97201',9.79,1.35,5),
('UPS','Ground','94301',9.49,1.30,5),
('UPS','Ground','10003',10.49,1.40,5),
('UPS','Ground','53704',8.99,1.25,4),
('UPS','Ground','94401',9.49,1.30,5),
('UPS','Ground','92101',9.29,1.30,5),
('UPS','Ground','02139',10.49,1.40,5),
('UPS','Ground','75024',8.99,1.25,4),
('UPS','Ground','94014',9.49,1.30,5),
('UPS','Ground','89501',9.79,1.35,5),
('UPS','Ground','95060',9.49,1.30,5),
('UPS','Ground','11201',10.49,1.40,5),
('UPS','Ground','90210',9.29,1.30,5),
('UPS','Ground','52245',8.49,1.20,4),
('UPS','Ground','52244',8.49,1.20,4),
('UPS','Ground','52240',8.49,1.20,4),
('UPS','Ground','52246',8.49,1.20,4),
('UPS','Ground','52241',8.49,1.20,4),
('UPS','Ground','99734',14.99,2.25,8),
('UPS','Ground','89049',9.79,1.35,5),
('UPS','Ground','99950',18.99,2.75,10),
('UPS','Ground','00501',11.49,1.50,6),
('UPS','Ground','77494',8.99,1.25,4),
('UPS','Ground','08701',10.29,1.40,5),
('UPS','Ground','77449',8.99,1.25,4),
('UPS','Ground','11368',10.49,1.40,5),
('UPS','Ground','90011',9.29,1.30,5),

-- USPS Services
('USPS','First Class','90210',5.49,0.85,3),
('USPS','Priority','90210',8.95,1.10,2),
('USPS','Priority Express','90210',22.95,1.50,1),

('USPS','First Class','10003',5.99,0.90,3),
('USPS','Priority','10003',9.45,1.15,2),
('USPS','Priority Express','10003',23.95,1.60,1),

-- FedEx Services
('FedEx','Ground','95112',9.75,1.30,5),
('FedEx','Home Delivery','95112',10.25,1.35,5),
('FedEx','Express Saver','95112',18.50,1.60,3),
('FedEx','2Day','95112',26.00,1.75,2),
('FedEx','Overnight','95112',42.00,2.25,1),

('FedEx','Ground','33101',11.25,1.45,6),
('FedEx','Express Saver','33101',19.95,1.70,3),
('FedEx','2Day','33101',27.95,1.85,2),

-- UPS Air Services
('UPS','2nd Day Air','78701',24.50,1.75,2),
('UPS','Next Day Air Saver','78701',38.00,2.10,1),
('UPS','Next Day Air','78701',48.00,2.40,1),

('UPS','2nd Day Air','60601',25.00,1.80,2),
('UPS','Next Day Air Saver','60601',39.50,2.15,1),

-- DHL Services
('DHL','Domestic Economy','94103',10.99,1.40,4),
('DHL','Domestic Express','94103',29.99,1.95,2),

('DHL','Domestic Economy','90011',10.49,1.35,4),
('DHL','Domestic Express','90011',28.99,1.90,2),

-- Regional / Economy Carriers
('OnTrac','Ground','92618',7.95,1.10,2),
('OnTrac','Express','92618',12.95,1.35,1),

('LaserShip','Ground','11201',8.49,1.20,2),
('LaserShip','Express','11201',14.99,1.50,1);
