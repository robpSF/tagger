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
            prompt = (f"Given what you know about this person - {persona} - which of these tags - {', '.join(tags)} - could be applied to the audience that follow them on social media?\n"
                      "##RULES\n"
                      "1. You must take tags from the list\n"
                      "2. If you don't know, return \"unknowable\"\n"
                      "##OUTPUT EXAMPLE\n"
                      "male, republican, under 35")
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
            # Initialize the progress bar
            progress_bar = st.progress(0)
            total_personas = len(personas_df)

            # Generate tags for each persona with progress tracking
            follower_tags = []
            for i, name in enumerate(personas_df['Name']):
                tags = get_tags_for_persona(name, unique_tags)
                follower_tags.append(tags)
                progress_bar.progress((i + 1) / total_personas)

            personas_df['Follower Tags'] = follower_tags
            st.success("Tags generated successfully!")

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
