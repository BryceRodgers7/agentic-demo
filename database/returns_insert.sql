-- =====================
-- NEW ORDERS (FOR RETURNS)
-- =====================

INSERT INTO orders
(customer_name, customer_email, customer_phone, shipping_address, zip_code, city, state, status, total_amount)
VALUES
('Aaron Blake','aaron.blake@email.com','555-2001','410 Cedar St','90028','Los Angeles','CA','delivered',399.00),
('Bianca Lopez','bianca.lopez@email.com','555-2002','77 Market St','94103','San Francisco','CA','delivered',249.00),
('Connor Mills','connor.mills@email.com','555-2003','18 Lakeview Dr','53703','Madison','WI','delivered',699.00),
('Danielle Frost','danielle.frost@email.com','555-2004','950 Union Ave','10003','New York','NY','delivered',1299.00),
('Ethan Wu','ethan.wu@email.com','555-2005','62 Willow Rd','92618','Irvine','CA','delivered',199.00);

-- =====================
-- RETURNS
-- =====================

INSERT INTO returns
(order_id, product_id, return_reason, status, refund_amount, processed_at)
VALUES
(26,1,'Noise cancellation performance did not meet expectations.','approved',399.00,'2025-01-04 10:15:00'),

(27,5,'Keyboard keys felt too stiff for extended typing sessions.','pending',249.00,NULL),

(28,4,'Monitor experienced intermittent signal loss at 144Hz.','approved',699.00,'2025-01-04 14:40:00'),

(29,7,'Speakers produced static noise at low volume levels.','rejected',0.00,'2025-01-05 09:30:00'),

(30,6,'Keyboard layout was smaller than expected for daily use.','approved',199.00,'2025-01-05 16:10:00');
