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

        # Print the array of unique tags for debugging
        st.write("Unique Tags:", unique_tags)

        def get_tags_for_persona(persona, tags):
            prompt = (f"Given the person {persona} and possible tags {', '.join(tags)}, which tags are most likely to "
                      f"identify the social media followers of {persona}. \n"
                      "##OUTPUT \n"
                      "Output to a CSV list of tags \n"
                      "##EXAMPLE \n"
                      "male, republican, under 30")
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
            personas_df['Follower Tags'] = personas_df['Name'].apply(lambda name: get_tags_for_persona(name, unique_tags))
            st.success("Tags generated successfully!")

            # Format the follower tags as CSV list
            personas_df['Follower Tags'] = personas_df['Follower Tags'].apply(lambda x: ', '.join([tag.strip() for tag in x.split(',')]))

            # Create a new table with Name, Handle, and Follower Tags
            result_df = personas_df[['Name', 'Handle', 'Follower Tags']]
            st.dataframe(result_df)

            # Save the results
            if st.button("Save Tags"):
                csv = result_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="tagged_personas.csv">Download CSV file</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success("Tags saved successfully!")
    else:
        st.warning('Please upload the Personas Excel file to proceed.')
else:
    st.warning('Please enter your OpenAI API key to proceed.')
