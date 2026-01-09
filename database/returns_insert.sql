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
