def make_prompt(
    customer, customer_information, n_words, target_audience, tone_of_voice, domain, seed_sentence
):
    prompt = f"""
        The following text contains relevant information for the company {customer}. Please read it carefully.
        {customer_information}

        These are the input parameters:
        * number_of_words: {n_words}
        * target_audience: {target_audience}
        * tone_of_voice: {tone_of_voice}
        * domain: {domain}
        * seed_sentence: {seed_sentence}

        Description of input parameters:
        * number_of_words: The number of words to be generated. 20 more or less is fine.
        * target_audience: The people who are supposed to read the text generated.
        * tone_of_voice: The tone of voice.
        * domain: The domain or context the generated text is for. Some examples could be advertisement, legal, b2b.
        * seed_sentence: Information from the user on what he wants to generate text for.

        It is important that the generated text uses the information provided together the input parameters and seed sentence to generate a text that is relevant to the company.
        The most important input parameter is the seed sentence.
        The generated text should be in markdown format.
    """

    return prompt
