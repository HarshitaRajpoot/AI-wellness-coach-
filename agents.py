from llm import get_response

def nutrition_agent(query, user_data, history):
    prompt = f"""
    You are a professional nutritionist.

    User Details:
    {user_data}

    Conversation:
    {history}

    Question: {query}

    Provide structured diet plan.
    """
    return get_response(prompt)


def workout_agent(query, user_data, history):
    prompt = f"""
    You are a professional fitness trainer.

    User Details:
    {user_data}

    Conversation:
    {history}

    Question: {query}

    Provide structured workout routine.
    """
    return get_response(prompt)


def route_query(query, user_data, history):
    from llm import get_response

    router_prompt = f"""
    Classify the query into:
    - diet
    - workout

    Query: {query}

    Answer in one word.
    """

    category = get_response(router_prompt).lower()

    if "diet" in category:
        return nutrition_agent(query, user_data, history)
    else:
        return workout_agent(query, user_data, history)