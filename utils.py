def only_digits(value):
    if value is None:
        return ""
    return "".join([c for c in str(value) if c.isdigit()])


def mask_cpf(cpf):
    if cpf is None:
        return ""
    digits = only_digits(cpf)
    if len(digits) < 2:
        return "***"
    return f"***.***.***-{digits[-2:]}"


def mask_phone(telefone):
    if telefone is None:
        return ""
    digits = only_digits(telefone)
    if len(digits) <= 4:
        return "****"
    return f"{'*' * (len(digits) - 4)}{digits[-4:]}"


def mask_email(email):
    if not email:
        return ""
    if "@" not in email:
        return email
    nome, dominio = email.split("@", 1)
    if len(nome) <= 1:
        masked_nome = "*"
    else:
        masked_nome = nome[0] + "*" * (len(nome) - 1)
    return f"{masked_nome}@{dominio}"


def mask_nome(nome):
    return nome or ""
