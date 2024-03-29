"""
Miscellaneous helper functions
"""

from cht import CURR_CONGRESS


# Generate ordinals from an integer
# From https://stackoverflow.com/questions/9647202/ordinal-numbers-replacement  
def ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        suffix = 'th'
    else:
        suffix = ['th', 'st', 'nd', 'rd', 'th'][min(n % 10, 4)]
    return str(n) + suffix

# Returns the congress number given a year
def to_congress(year: int) -> int:
    congress = (year - 1789) // 2 + 1

    return congress

# Checks if the given Congress is valid for this tool
def valid_congress(congress: int) -> bool:
    return congress > 104 and congress < CURR_CONGRESS

# Get congress from govinfo ID
def congress_from_id(id: str) -> int:
    congress_str = ''
    for char in id:
        if char.isdigit():
            congress_str += char
        elif len(congress_str) > 0:
            break
    
    return int(congress_str)