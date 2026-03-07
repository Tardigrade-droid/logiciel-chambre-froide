"""Utilitaires pour l'application"""

def format_currency(amount, currency="FC"):
    """
    Formate un montant d'argent avec séparateurs de milliers.
    
    Args:
        amount: Le montant à formater (int ou float)
        currency: La devise à afficher (défaut: "FC")
    
    Returns:
        Chaîne formatée avec séparateurs (ex: "1 234,50 FC")
    
    Exemples:
        >>> format_currency(1234.5)
        '1 234,50 FC'
        >>> format_currency(1000000.99)
        '1 000 000,99 FC'
        >>> format_currency(42.1)
        '42,10 FC'
    """
    try:
        # Formater avec 2 décimales
        formatted = f"{float(amount):,.2f}"
        
        # Remplacer la virgule et le point pour le format français
        # from "1,234.50" to "1 234,50"
        parts = formatted.split('.')
        integer_part = parts[0].replace(',', ' ')  # Remplacer virgules par espaces
        decimal_part = parts[1] if len(parts) > 1 else "00"
        
        return f"{integer_part},{decimal_part} {currency}"
    except (ValueError, TypeError):
        return f"0,00 {currency}"
