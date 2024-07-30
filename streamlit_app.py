import streamlit as st
import pandas as pd
import openai
import base64
from io import BytesIO

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

# Function to convert DataFrame to Excel
def to_excel(df):
    output = BytesIO()
    writer = pd.ExcelWriter(output, engine='xlsxwriter')
    df.to_excel(writer, index=False, sheet_name='Sheet1')
    writer.save()
    processed_data = output.getvalue()
    return processed_data

# Function to find possible followers
def find_possible_followers(persona_tags, all_personas, min_matches=2):
    possible_followers = []
    for _, follower in all_personas.iterrows():
        follower_tags = follower['Tags'].split(', ')
        match_count = sum(1 for tag in persona_tags if tag in follower_tags)
        if match_count >= min_matches and match_count < len(persona_tags):
            possible_followers.append((follower['Name'], follower['Handle'], match_count))
    return possible_followers

# Function to apply probability and rank followers
def apply_probability_and_rank(followers, probability):
    followers.sort(key=lambda x: x[2], reverse=True)  # Sort by match_count
    num_to_select = int(len(followers) * probability)
    return followers[:num_to_select]

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

        # Multiselect widget for removing generic tags
        tags_to_remove = st.multiselect('Select tags to remove', unique_tags)

        # Remove selected tags from the unique tags list
        filtered_tags = [tag for tag in unique_tags if tag not in tags_to_remove]

        # Print the array of filtered tags for debugging
        st.write("Filtered Tags:", filtered_tags)

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
                tags = get_tags_for_persona(name, filtered_tags)
                follower_tags.append(tags)
                progress_bar.progress((i + 1) / total_personas)

            # Merge the tags back to the main DataFrame
            personas_df['Follower Tags'] = personas_df['Name'].map(dict(zip(filtered_personas_df['Name'], follower_tags))).fillna('')

            # Calculate the probability for each persona based on TwFollowers
            personas_df['Probability'] = personas_df['TwFollowers'].apply(calculate_probability)

            st.success("Tags and probabilities generated successfully!")

            # Generate possible followers for each persona
            results = []
            for _, persona in personas_with_tags.iterrows():
                persona_name = persona['Name']
                persona_tags = persona['Follower Tags'].split(', ')
                possible_followers = find_possible_followers(persona_tags, personas_df)
                likely_followers = apply_probability_and_rank(possible_followers, persona['Probability'])
                for follower in likely_followers:
                    results.append({'Follower': follower[0], 'Follower Handle': follower[1], 'Followed Persona': persona_name})

            results_df = pd.DataFrame(results)
            st.dataframe(results_df)

            # Save the results as CSV and Excel
            if st.button("Save as CSV"):
                csv = results_df.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="tagged_personas.csv">Download CSV file</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success("CSV file saved successfully!")

            excel_data = to_excel(results_df)
            st.download_button(
                label="Download Filtered Data as Excel",
                data=excel_data,
                file_name='tagged_personas.xlsx',
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
    else:
        st.warning('Please upload the Personas Excel file to proceed.')
else:
    st.warning('Please enter your OpenAI API key to proceed.')
