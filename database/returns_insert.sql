-- =====================
-- RETURNS
-- =====================

-- Return Orders
INSERT INTO agent_return_orders
(order_id, return_reason, status, refund_total_amount, processed_at)
VALUES
(26, 'Noise cancellation performance did not meet expectations.', 'approved', 399.00, '2025-01-04 10:15:00'),
(27, 'Keyboard keys felt too stiff for extended typing sessions.', 'pending', 249.00, NULL),
(28, 'Monitor experienced intermittent signal loss at 144Hz.', 'approved', 699.00, '2025-01-04 14:40:00'),
(29, 'Speakers produced static noise at low volume levels.', 'rejected', 0.00, '2025-01-05 09:30:00'),
(30, 'Keyboard layout was smaller than expected for daily use.', 'approved', 199.00, '2025-01-05 16:10:00');

-- Return Items (linking returns to specific products with quantities)
-- Note: These examples assume single-item returns. For multi-item returns, add multiple rows with same return_id
INSERT INTO agent_return_items
(return_id, product_id, quantity, price_at_purchase)
VALUES
-- Return #1: Aether X1 Headphones from order 26
(1, 1, 1, 399.00),

-- Return #2: Orion Mechanical Keyboard from order 27
(2, 5, 1, 249.00),

-- Return #3: Lumina 27 Edge Monitor from order 28
(3, 4, 1, 699.00),

-- Return #4: Nova Studio Speakers from order 29 (rejected)
(4, 7, 1, 599.00),

-- Return #5: Orion Mini Keyboard from order 30
(5, 6, 1, 199.00);
