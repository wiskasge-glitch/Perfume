# Puntaje mínimo necesario para enviar una oferta.
MIN_ALERT_SCORE = 60.0

# Puntos generales.
TRUSTED_SELLER_POINTS = 15.0
MERCADO_LIDER_POINTS = 10.0
FULL_POINTS = 8.0
NEW_CONDITION_POINTS = 5.0
REFERENCE_PRICE_POINTS = 2.0

# Se requieren al menos tres precios anteriores
# para considerar confiable el historial.
MIN_HISTORY_OBSERVATIONS = 3

# Porcentaje mínimo de descuento y puntos asignados.
# Se revisan de arriba hacia abajo.
DISCOUNT_SCORE_BANDS = (
    (30.0, 30.0),
    (25.0, 26.0),
    (20.0, 22.0),
    (15.0, 17.0),
    (10.0, 12.0),
    (5.0, 6.0),
)

# Clasificación final de la oferta.
SCORE_LEVELS = (
    (85.0, "Excelente"),
    (70.0, "Muy buena"),
    (55.0, "Interesante"),
    (0.0, "Baja"),
)