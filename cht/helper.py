"""
Miscellaneous helper functions
"""


# Generate ordinals from an integer
# From https://stackoverflow.com/questions/9647202/ordinal-numbers-replacement  
def ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix