"""
Constants related to loyalty facts APIs
"""

TRANSACTION_RESOLVE_DECISIONS = {
    1: 'accrual',
    2: 'redemption'
}

TRANSACTION_RESOLVE_STATUS_CODE_MESSAGES = {
    0: 'Transaction resolution request submitted',
    1: 'Input validation failed',
    2: 'The transaction id is not associated with an open transaction',
}
