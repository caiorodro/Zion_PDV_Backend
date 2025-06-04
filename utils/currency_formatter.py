def format_currency(value: float) -> str:
    """
    Formata um número como moeda brasileira (R$), sem usar o módulo locale.

    :param value: O número (float ou int) a ser formatado.
    :return: String formatada como moeda.
    """
    # Certifica-se de que o número é tratado como float
    value = float(value)

    # Formata o número com 2 casas decimais, separadores de milhares e vírgula como separador decimal
    formatted = f"{value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")

    # Adiciona o símbolo da moeda e retorna
    if value < 0:
        return f"R$ ({formatted[1:]})"  # Remove o sinal '-' e adiciona parênteses
    return f"R$ {formatted}"
