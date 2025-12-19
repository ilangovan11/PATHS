def resolve_action(prediction, confidence, raw_input):
    attendance, marks, assignments, study_hours, backlogs, stress = raw_input

    if attendance < 50 or (backlogs >= 5 and stress >= 8):
        return "RETREAT", "Critical risk detected by rule override"

    if confidence < 0.6:
        return "HOLD", "Low confidence in prediction"

    if prediction == 0:
        return "ADVANCE", "Performance indicators are stable"

    if prediction == 1:
        return "HOLD", "Moderate risk requires monitoring"

    return "RETREAT", "High risk predicted by model"
