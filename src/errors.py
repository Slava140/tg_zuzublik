class SuffixNotAllowedError(Exception):
    def __init__(self):
        super().__init__('Suffix is not allowed.')


class InvalidDocumentSchemaError(Exception):
    def __init__(self):
        super().__init__('Invalid document schema')


class UnableToReadError(Exception):
    def __init__(self):
        super().__init__('Unable to read document')