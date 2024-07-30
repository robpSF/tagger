import streamlit as st
import pandas as pd
import openai
import base64

# Function to extract unique tags
def extract_unique_tags(tags_series):
    all_tags = set()
    tags_series.dropna().apply(lambda x: [all_tags.add(tag.strip()) for tag in x.split(',')])
    return sorted(all_tags)

# Input field for OpenAI API key
openai_api_key = st.text_input('Enter your OpenAI API Key', type='password')

if openai_api_key:
    openai.api_key = openai_api_key

    st.title("Persona Demographic Tagging")

    # File uploader for personas
    personas_file = st.file_uploader("Upload Personas Excel File", type="xlsx")

    if personas_file:
        personas_df = pd.read_excel(personas_file)
        unique_tags = extract_unique_tags(personas_df['Tags'])

        def get_tags_for_persona(persona, tags):
            prompt = f"Given the persona {persona} and possible tags {', '.join(tags)}, provide the likely demographics (e.g., age, gender) of the followers."
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
            personas_df['Tags'] = personas_df['Name'].apply(lambda name: get_tags_for_persona(name, unique_tags))
            st.success("Tags generated successfully!")

        # Display and Edit Tags
        for i, row in personas_df.iterrows():
            st.subheader(row['Name'])
            tags = st.text_input(f"Tags for {row['Name']}", row['Tags'] if 'Tags' in row else '')
            personas_df.at[i, 'Tags'] = tags

        # Save the results
        if st.button("Save Tags"):
            csv = personas_df.to_csv(index=False)
            b64 = base64.b64encode(csv.encode()).decode()
            href = f'<a href="data:file/csv;base64,{b64}" download="tagged_personas.csv">Download CSV file</a>'
            st.markdown(href, unsafe_allow_html=True)
            st.success("Tags saved successfully!")

        st.dataframe(personas_df)
    else:
        st.warning('Please upload the Personas Excel file to proceed.')
else:
    st.warning('Please enter your OpenAI API key to proceed.')
