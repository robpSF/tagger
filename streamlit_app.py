import streamlit as st
import pandas as pd
import openai
import base64

# Function to extract unique tags
def extract_unique_tags(tags_series):
    all_tags = set()
    tags_series.dropna().apply(lambda x: [all_tags.add(tag.strip()) for tag in x.split(',')])
    return sorted(all_tags)

# Function to calculate probability based on TwFollowers
def calculate_probability(tw_followers):
    if tw_followers < 1000:
        return 0.1
    elif 1000 <= tw_followers < 5000:
        return 0.2
    elif 5000 <= tw_followers < 10000:
        return 0.3
    elif 10000 <= tw_followers < 50000:
        return 0.4
    elif 50000 <= tw_followers < 100000:
        return 0.5
    elif 100000 <= tw_followers < 500000:
        return 0.6
    elif 500000 <= tw_followers < 1000000:
        return 0.7
    elif 1000000 <= tw_followers < 4000000:
        return 0.8
    elif 4000000 <= tw_followers < 8000000:
        return 0.9
    else:
        return 1.0

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
            # Filter personas based on faction starting with '_'
            filtered_personas_df = personas_df[personas_df['Faction'].str.startswith('_', na=False)]
            total_personas = len(filtered_personas_df)

            # Initialize the progress bar
            progress_bar = st.progress(0)

            # Generate tags for each persona with progress tracking
            follower_tags = []
            for i, row in filtered_personas_df.iterrows():
                name = row['Name']
                tags = get_tags_for_persona(name, unique_tags)
                follower_tags.append(tags)
                progress_bar.progress((i + 1) / total_personas)

            # Merge the tags back to the main DataFrame
            personas_df['Follower Tags'] = personas_df['Name'].map(dict(zip(filtered_personas_df['Name'], follower_tags))).fillna('')

            # Calculate the probability for each persona based on TwFollowers
            personas_df['Probability'] = personas_df['TwFollowers'].apply(calculate_probability)

            st.success("Tags and probabilities generated successfully!")

            # Create a new table with Name, Handle, Follower Tags, and Probability
            result_df = personas_df[['Name', 'Handle', 'Follower Tags', 'Probability']]
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
