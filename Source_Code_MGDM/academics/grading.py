# academics/grading.py

def calculate_grade(percentage):
    """
    Calculates the grade point and letter grade based on a percentage.
    """
    if percentage >= 90: return ('SA', 10)
    if percentage >= 80: return ('AA', 9)
    if percentage >= 70: return ('AB', 8)
    if percentage >= 60: return ('BB', 7)
    if percentage >= 50: return ('BC', 6)
    if percentage >= 40: return ('CC', 5)
    if percentage >= 30: return ('CD', 4)
    return ('FF', 0) # Fail
