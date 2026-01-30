-- =====================
-- ORDERS
-- =====================

INSERT INTO agent_orders
(customer_name, customer_email, customer_phone, shipping_address, zip_code, city, state, status, total_amount)
VALUES
('Alice Morgan','alice.morgan@email.com','555-1001','12 Oak St','80202','Denver','CO','shipped',1597.00),
('Brian Chen','bchen@email.com','555-1002','88 Pine Rd','95112','San Jose','CA','processing',249.00),
('Carla Ruiz','cruiz@email.com','555-1003','441 Sunset Blvd','90028','Los Angeles','CA','delivered',899.00),
('David Patel','dpatel@email.com','555-1004','901 Market St','94103','San Francisco','CA','pending',299.00),
('Emily Stone','estone@email.com','555-1005','77 Beacon St','02108','Boston','MA','shipped',1299.00),
('Frank Howard','fhoward@email.com','555-1006','300 Lake Dr','53703','Madison','WI','delivered',598.00),
('Grace Kim','gkim@email.com','555-1007','19 Elm Ave','98101','Seattle','WA','processing',2199.00),
('Henry Walsh','hwalsh@email.com','555-1008','602 River Rd','78701','Austin','TX','pending',399.00),
('Isabel Flores','iflores@email.com','555-1009','145 Palm Way','33101','Miami','FL','delivered',699.00),
('Jack Turner','jturner@email.com','555-1010','811 Ridge Ln','80302','Boulder','CO','shipped',1148.00),
('Karen Li','kli@email.com','555-1011','9 Maple Ct','92618','Irvine','CA','processing',199.00),
('Leo Novak','lnovak@email.com','555-1012','55 Birch Rd','60601','Chicago','IL','pending',349.00),
('Maya Singh','msingh@email.com','555-1013','210 Ash St','94538','Fremont','CA','delivered',249.00),
('Noah Bennett','nbennett@email.com','555-1014','18 Forest Dr','97201','Portland','OR','shipped',179.00),
('Olivia Park','opark@email.com','555-1015','920 Willow St','94301','Palo Alto','CA','processing',499.00),
('Paul Adams','padams@email.com','555-1016','67 Union Sq','10003','New York','NY','pending',199.00),
('Quinn Rogers','qrogers@email.com','555-1017','130 Lakeview Rd','53704','Madison','WI','delivered',399.00),
('Rina Shah','rshah@email.com','555-1018','45 Orchard St','94401','San Mateo','CA','shipped',229.00),
('Samuel Ortiz','sortiz@email.com','555-1019','700 Mission St','92101','San Diego','CA','processing',699.00),
('Tina Brooks','tbrooks@email.com','555-1020','22 Highland Ave','02139','Cambridge','MA','pending',149.00),
('Umar Khan','ukhan@email.com','555-1021','310 Cedar Dr','75024','Plano','TX','delivered',1799.00),
('Violet Nguyen','vnguyen@email.com','555-1022','58 Spruce St','94014','Daly City','CA','shipped',298.00),
('Will Carter','wcarter@email.com','555-1023','901 Hilltop Rd','89501','Reno','NV','processing',1299.00),
('Xena Morales','xmorales@email.com','555-1024','14 Bay St','95060','Santa Cruz','CA','pending',448.00),
('Yusuf Ali','yali@email.com','555-1025','620 Pearl St','11201','Brooklyn','NY','delivered',999.00);


-- =====================
-- ORDER ITEMS
-- =====================

INSERT INTO agent_order_items (order_id, product_id, quantity, price_at_purchase) VALUES
-- Order 1
(1,1,1,399.00),(1,3,1,899.00),(1,20,1,149.00),(1,10,1,199.00),

-- Order 2
(2,5,1,249.00),

-- Order 3
(3,3,1,899.00),

-- Order 4
(4,19,1,299.00),

-- Order 5
(5,7,1,1299.00),

-- Order 6
(6,11,2,199.00),

-- Order 7
(7,2,1,2199.00),

-- Order 8
(8,1,1,399.00),

-- Order 9
(9,4,1,699.00),

-- Order 10
(10,1,1,399.00),(10,6,1,199.00),(10,11,1,199.00),(10,16,1,349.00),

-- Order 11
(11,6,1,199.00),

-- Order 12
(12,16,1,349.00),

-- Order 13
(13,9,1,249.00),

-- Order 14
(14,18,1,179.00),

-- Order 15
(15,13,1,499.00),

-- Order 16
(16,10,2,99.00),

-- Order 17
(17,15,1,399.00),

-- Order 18
(18,14,1,229.00),

-- Order 19
(19,8,1,699.00),

-- Order 20
(20,20,1,149.00),

-- Order 21
(21,2,1,2199.00),(21,19,1,299.00),(21,10,1,199.00),(21,6,1,199.00),

-- Order 22
(22,10,2,99.00),(22,18,1,179.00),

-- Order 23
(23,7,1,1299.00),

-- Order 24
(24,5,1,249.00),(24,6,1,199.00),

-- Order 25
(25,3,1,899.00),(25,10,1,99.00);


-- =====================
-- NEW ORDERS (FOR RETURNS)
-- =====================

INSERT INTO agent_orders
(customer_name, customer_email, customer_phone, shipping_address, zip_code, city, state, status, total_amount)
VALUES
('Aaron Blake','aaron.blake@email.com','555-2001','410 Cedar St','90028','Los Angeles','CA','delivered',399.00),
('Bianca Lopez','bianca.lopez@email.com','555-2002','77 Market St','94103','San Francisco','CA','delivered',249.00),
('Connor Mills','connor.mills@email.com','555-2003','18 Lakeview Dr','53703','Madison','WI','delivered',699.00),
('Danielle Frost','danielle.frost@email.com','555-2004','950 Union Ave','10003','New York','NY','delivered',1299.00),
('Ethan Wu','ethan.wu@email.com','555-2005','62 Willow Rd','92618','Irvine','CA','delivered',199.00);

INSERT INTO agent_order_items (order_id, product_id, quantity, price_at_purchase)
VALUES
-- Order 26 (Aether X1 returned, additional item kept)
(26,1,1,399.00),
(26,10,1,199.00),

-- Order 27 (Orion Mechanical Keyboard returned, earbuds kept)
(27,5,1,249.00),
(27,9,1,249.00),

-- Order 28 (Lumina 27 Edge returned, webcam kept)
(28,4,1,699.00),
(28,10,1,199.00),

-- Order 29 (Nova Studio Speakers attempted return, camera body kept)
(29,7,1,1299.00),
(29,2,1,2199.00),

-- Order 30 (Orion Mini returned, monitor arm kept)
(30,6,1,199.00),
(30,20,1,149.00);
