import streamlit as st
import pandas as pd
import openai

# Input field for OpenAI API key
openai_api_key = st.text_input('Enter your OpenAI API Key', type='password')

if openai_api_key:
    openai.api_key = openai_api_key

    st.title("Persona Demographic Tagging")

    # File uploader for personas
    personas_file = st.file_uploader("Upload Personas CSV", type="csv")
    tags_file = st.file_uploader("Upload Tags CSV", type="csv")

    if personas_file and tags_file:
        personas_df = pd.read_csv(personas_file)
        tags_df = pd.read_csv(tags_file)

        def get_tags_for_persona(persona):
            prompt = f"Provide the likely demographics (e.g., age, gender) of the followers for the following persona: {persona}"
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150
            )
            return response.choices[0].message['content']

        if st.button("Generate Tags for All Personas"):
            personas_df['Tags'] = personas_df['Persona'].apply(get_tags_for_persona)
            st.success("Tags generated successfully!")

        # Display and Edit Tags
        for i, row in personas_df.iterrows():
            st.subheader(row['Persona'])
            tags = st.text_input(f"Tags for {row['Persona']}", row['Tags'] if 'Tags' in row else '')
            personas_df.at[i, 'Tags'] = tags

        # Save the results
        if st.button("Save Tags"):
            personas_df.to_csv('data/tagged_personas.csv', index=False)
            st.success("Tags saved successfully!")

        st.dataframe(personas_df)
    else:
        st.warning('Please upload both Personas and Tags CSV files to proceed.')
else:
    st.warning('Please enter your OpenAI API key to proceed.')
