import pandas as pd
import random
import datetime

ROWS = 1500

# -----------------------------
# Indian Names (realistic)
# -----------------------------

first_names = [
    "Amit","Rahul","Rohit","Ankit","Suresh","Ramesh","Vikas","Arjun","Karan","Vivek",
    "Neha","Pooja","Anjali","Kavita","Ritu","Sneha","Priya","Shivam","Aditya","Manish",
    "Nitin","Aakash","Sanjay","Deepak","Abhishek","Ayush","Kunal","Mohit","Riya","Nisha"
]

last_names = [
    "Sharma","Verma","Singh","Yadav","Gupta","Mishra","Pandey","Tiwari","Chaudhary",
    "Agarwal","Jain","Srivastava","Tripathi","Saxena","Malhotra","Kapoor","Kumar",
    "Rastogi","Bansal","Mehta"
]

def random_indian_name():
    return f"{random.choice(first_names)} {random.choice(last_names)}"


# -----------------------------
# Form Enums
# -----------------------------

classes = ["6 th","7 th","8 th","9 th","10 th","11th","12th"]
study_time = ["<2 Hrs","2-3 Hrs","3-4 Hrs","More than 4 Hrs"]

subject_groups = ["Maths","Biology","IT/CS","Commerce","Not Applicable"]

subjects_all = [
    "Hindi","English","Maths","Science","Social Science",
    "Physics","Chemistry","Biology","IT/CS","Business Studies",
    "Accountancy","Economics","Other"
]

agree_scale = ["Strongly agree","Agree","Neutral","Disagree","Strongly disagree"]
realworld = ["Excellent","Good","Average","Poor","Very poor"]

extra = ["Very sufficient","Sufficient","Neutral","Insufficient","Very insufficient"]
transport = ["Very satisfied","Satisfied","Neutral","Dissatisfied","Very dissatisfied"]

bullying = ["Very well","Well","Adequately","Poorly","Very poorly"]
fee = ["Strongly positive","Positive","Neutral","Negative","Strongly negative"]

teaching = ["Highly satisfied","Satisfied","Somewhat satisfied","Not satisfied","Extremely dissatisfied"]


def pick(n):
    return ", ".join(random.sample(subjects_all, n))


# -----------------------------
# Long Open-Ended Feedback Templates (for 25% of responses)
# These are realistic, detailed student feedback responses
# -----------------------------

LONG_TEACHER_FEEDBACK = [
    "I feel that our mathematics teacher is very good at explaining concepts, but sometimes the pace is too fast for students who are not naturally strong in math. It would be helpful if the teacher could spend more time on difficult topics like trigonometry and algebra. Also, more practice problems during class would really help us understand better.",
    
    "The science teacher makes learning very interesting with experiments and real-life examples. However, I think we need more practical lab sessions to really understand the concepts. Sometimes the theory classes can get boring without any hands-on activities. I suggest having at least two lab sessions per week instead of one.",
    
    "Our English teacher is excellent at teaching grammar and writing skills, but I feel we need more focus on spoken English and communication. Many students in our class struggle with speaking confidently in English. Perhaps we could have regular debates or presentations to improve our speaking abilities.",
    
    "I appreciate how our Hindi teacher explains classical literature and poetry with so much passion. However, the examination pattern focuses too much on rote memorization rather than understanding. It would be better if we could discuss the meanings and interpretations more during class instead of just memorizing answers.",
    
    "The physics teacher is knowledgeable but often uses very complex language that is difficult for us to understand. I wish the explanations were more simple and included more diagrams and visual aids. Also, connecting physics concepts to everyday life situations would make it much more interesting for students.",
    
    "I really like how our chemistry teacher conducts experiments and demonstrations in class. It makes learning very engaging. My only suggestion is that we should have more time for individual practice in the lab, as currently we only observe the teacher doing experiments most of the time.",
    
    "The social science teacher makes history very interesting with stories and anecdotes, but geography classes are quite boring with just reading from the textbook. I think using maps, videos, and interactive tools would make geography more engaging for students like me who find it difficult.",
    
    "Our computer science teacher is very patient and explains programming concepts clearly. However, we have very limited computer access and have to share systems during practicals. This makes it difficult to practice coding properly. I hope the school can provide more computers for the lab.",
    
    "I think the biology teacher should use more visual aids like videos and 3D models to explain complex topics like human anatomy and cell biology. Reading from textbooks alone is not enough for us to truly understand these concepts. More interactive teaching methods would be very helpful.",
    
    "The accountancy teacher is good at explaining numerical problems, but rushes through theoretical concepts. Many students including me struggle with the theory portion in exams. It would help if equal time was given to both theory and practical numerical problems during class.",
    
    "I appreciate that teachers are always available for doubt solving after class, but I feel that students who are shy don't get enough attention during regular class hours. Maybe teachers could check on quieter students more often to see if they are following the lessons properly.",
    
    "Our economics teacher makes the subject very interesting by discussing current events and news. However, sometimes the discussions go off-topic and we don't cover the syllabus properly. I suggest having a better balance between current events and textbook concepts.",
    
    "The physical education teacher is very encouraging and helps build confidence in sports. However, I feel that students who are not naturally athletic get ignored sometimes. It would be nice if there were activities suitable for all fitness levels, not just competitive sports.",
    
    "I feel that some teachers give too much homework without considering that we have multiple subjects to study. It becomes overwhelming especially before exams when we have to complete assignments and also prepare for tests. Better coordination among teachers regarding homework would really help.",
    
    "Our class teacher is very supportive and always listens to our problems patiently. I really appreciate how she handles conflicts between students fairly and creates a positive classroom environment. More teachers should follow her approach of being approachable and understanding."
]

LONG_SCHOOL_FEEDBACK = [
    "I believe our school has excellent academic standards, but there is too much pressure on students to perform well in exams. The focus on marks over actual learning creates stress and anxiety among many students including myself. I think the school should promote a more balanced approach to education that values understanding over memorization.",
    
    "The school infrastructure is quite good with nice classrooms and sports facilities. However, the library is not well-stocked with recent books and study materials. Many reference books are outdated and we have to rely on external sources for competitive exam preparation. Updating the library collection would greatly benefit students.",
    
    "I appreciate that our school organizes various cultural and sports events throughout the year. These activities help us develop skills beyond academics. However, I feel that participation in these events should be encouraged more, as currently only a few talented students get opportunities while others are overlooked.",
    
    "The school cafeteria food quality has been declining over the past few months. The meals are often repetitive and not very nutritious. As students who spend most of our day at school, we need proper healthy food to stay focused during classes. I request the management to look into improving the food quality.",
    
    "Transportation facilities provided by the school are generally good, but the buses are overcrowded during peak hours. This makes the commute uncomfortable and sometimes unsafe. Adding more buses or adjusting routes could help distribute students better and improve the travel experience.",
    
    "I feel that our school should focus more on environmental awareness and sustainability practices. We could start with basic things like proper waste segregation, reducing plastic usage, and planting more trees in the campus. This would teach students important values while making our school more eco-friendly.",
    
    "The school's approach to handling disciplinary issues is sometimes too strict without understanding the context. Students are punished for minor mistakes without being given a chance to explain. A more understanding and counseling-based approach would be better than strict punishments.",
    
    "Career guidance and counseling services in our school need significant improvement. Many students in senior classes are confused about their future options and don't know what courses to pursue. Regular career counseling sessions with professionals from different fields would help us make informed decisions.",
    
    "I appreciate the recent addition of smart classrooms with projectors and interactive boards. These have made learning much more engaging and interesting. However, technical issues are common and sometimes entire classes are wasted due to equipment problems. Better maintenance support is needed.",
    
    "The school playground and sports facilities are good, but access is limited mostly to students who are part of sports teams. Regular students don't get enough opportunity to use these facilities during breaks or free periods. More open access would encourage physical activity among all students.",
    
    "Our school should organize more educational trips and excursions. Learning through experiences is much more effective than classroom teaching alone. Visits to museums, science centers, historical places, and even industries related to our subjects would enhance our understanding significantly.",
    
    "I think the school needs to address the issue of bullying more seriously. While teachers try to resolve conflicts, there is no proper system for students to report incidents confidentially. A dedicated counselor or helpline for such issues would make students feel safer.",
    
    "The school should improve its communication with parents about student progress. Currently, parent-teacher meetings happen only twice a year which is not enough. Regular updates through apps or portals would help parents stay informed and support their children's education better.",
    
    "Medical facilities in our school need improvement. The medical room is not well-equipped and the nurse is not always available. Given that many students have health issues or emergencies during school hours, having proper first aid facilities and trained staff is very important.",
    
    "I feel that the school timings are too long and exhausting for students. Starting early in the morning and ending late in the afternoon leaves very little time for self-study, hobbies, or rest. Shorter school hours with more efficient teaching could improve both learning and well-being."
]

LONG_SCHOOL_SUGGESTIONS = [
    "I strongly suggest that our school should introduce more vocational training and skill development courses alongside regular academics. Subjects like basic coding, financial literacy, communication skills, and practical life skills would prepare us better for the real world. Many students don't want to pursue traditional academic paths and need alternative options.",
    
    "The school should organize regular workshops and seminars with industry professionals and alumni who have succeeded in different fields. Hearing from people who have practical experience would inspire students and give us better insights into various career paths available after school.",
    
    "I suggest implementing a peer tutoring program where academically strong students can help those who are struggling. This would benefit both groups - tutors would reinforce their learning while tutees would get extra help in a comfortable environment from their peers.",
    
    "Our school should have better facilities for students interested in arts and creative fields. Currently, there is too much emphasis on science and commerce while arts students are neglected. A proper art room, music room with instruments, and dedicated teachers for creative subjects would be very helpful.",
    
    "I recommend that the school starts a student council with real decision-making powers. Currently, decisions about school events and policies are made without any student input. Involving students in planning would make us more responsible and ensure that our needs are considered.",
    
    "The school should introduce mental health awareness programs and have a full-time counselor available for students. Academic pressure, family issues, and social problems affect many students but there is no proper support system. Regular sessions on stress management and emotional well-being would help everyone.",
    
    "I suggest having more flexible subject combinations and allowing students to choose electives based on their interests rather than rigid streams. For example, a commerce student interested in psychology should be able to take it as an optional subject without changing their entire stream.",
    
    "The school library should have extended hours and a more comfortable reading environment. Currently, it closes early and there are not enough seats for students who want to study there. Creating a quiet, well-lit study space with individual desks would benefit many students.",
    
    "Our school should partner with coaching institutes or provide special classes for competitive exam preparation like JEE, NEET, and CLAT. Many students have to take expensive external coaching which is a financial burden. In-school preparation programs would level the playing field for all students.",
    
    "I suggest implementing a proper feedback system where students can anonymously share their concerns and suggestions about teachers and school policies. Currently, there is no official channel for students to voice their opinions without fear of consequences. Regular surveys would help improve school quality.",
    
    "The school should organize more inter-school competitions and exchange programs. Interacting with students from other schools would broaden our perspectives and help develop important social skills. Currently, we are limited to competing only within our school which limits our exposure.",
    
    "I recommend that the school starts an entrepreneurship club where students interested in business can learn about starting their own ventures. With guidance from business mentors and opportunities to work on small projects, students could develop practical business skills from an early age.",
    
    "Our school should improve its digital infrastructure and provide better internet connectivity for students. In today's world, access to online resources is essential for learning. A dedicated computer lab with good internet available during free periods would help students research and learn independently.",
    
    "I suggest that the school should reconsider its strict uniform and grooming policies. While maintaining discipline is important, some rules about hair length and accessories seem unnecessary and don't affect our ability to learn. A more relaxed approach would be appreciated by students.",
    
    "The school should focus more on practical learning and reduce the emphasis on written exams alone. Project-based assessments, presentations, and group activities would help develop critical thinking and teamwork skills that are important in real life. Not everything should be judged by exam marks alone."
]

# Short feedback options (for 75% of responses)
SHORT_TEACHER_FEEDBACK = [
    "No concerns",
    "Need more examples",
    "Better revision needed",
    "Improve punctuality",
    "Good teaching overall",
    "Need more practice problems",
    "Classes are too fast",
    "Want more doubt sessions",
    "Teachers are helpful",
    "Need more explanation"
]

SHORT_SCHOOL_FEEDBACK = [
    "Need better labs",
    "More sports facilities",
    "Improve library",
    "No concerns",
    "Good infrastructure",
    "Better canteen food needed",
    "Improve transport",
    "More activities needed",
    "Clean washrooms needed",
    "Good overall"
]

SHORT_SCHOOL_SUGGESTIONS = [
    "Everything good",
    "Improve teaching",
    "More activities",
    "Reduce pressure",
    "Better facilities",
    "More sports events",
    "Improve labs",
    "Better career guidance",
    "More field trips",
    "No suggestions"
]


def get_feedback(long_options, short_options, long_probability=0.25):
    """
    Returns either a long detailed feedback (25% probability) 
    or a short feedback (75% probability)
    """
    if random.random() < long_probability:
        return random.choice(long_options)
    else:
        return random.choice(short_options)


# -----------------------------
# Roll Number Generator
# -----------------------------
def generate_roll_number(school_code, index):
    """
    Generate 6-digit roll number with pattern
    Format: SCYYYY where SC is school code (2 digits) and YYYY is sequential (4 digits)
    JNV VARANASI: starts with 10
    DPS VARANASI: starts with 20
    """
    return f"{school_code}{index:04d}"


# -----------------------------
# Generate rows
# -----------------------------

data = []
used_combinations = set()  # Track (roll_number, school_name) combinations

# Generate for JNV VARANASI (first 750 students)
for i in range(750):
    roll_number = generate_roll_number(10, i + 1)
    school_name = "JNV VARANASI"
    
    # Ensure uniqueness
    while (roll_number, school_name) in used_combinations:
        roll_number = generate_roll_number(10, random.randint(1, 9999))
    
    used_combinations.add((roll_number, school_name))
    
    ts = (datetime.datetime.now() - datetime.timedelta(
        minutes=random.randint(1, 600000)
    )).strftime("%d/%m/%Y %H:%M:%S")

    row = {
        "Timestamp": ts,
        "Your name": random_indian_name(),
        "Roll Number": roll_number,
        "Your school name": school_name,
        "Your class": random.choice(classes),
        "What was your last year overall percentage or CGPA?": random.randint(5, 10),
        "How much time do you spend every day on your self study and homework?": random.choice(study_time),
        "Which is your least favourite or toughest subject?": random.choice(subjects_all),
        "Subject group": random.choice(subject_groups),

        "Choose Subject Where The Subject Teacher Rating is [Excellent]": pick(2),
        "Choose Subject Where The Subject Teacher Rating is [Very Good]": pick(2),
        "Choose Subject Where The Subject Teacher Rating is [Good]": pick(2),
        "Choose Subject Where The Subject Teacher Rating is [Average]": pick(2),
        "Choose Subject Where The Subject Teacher Rating is [Poor]": pick(1),

        "Do teachers provide enough support for your academic learning and solving queries?": random.choice(agree_scale),
        "How do you meet your academic learning goal?": random.choice([
            "School only","Coaching from existing faculty","Coaching from outside faculty",
            "Online coaching","Internet materials","Reference or side books"
        ]),
        "How well do teachers give real-world applications or examples in class?": random.choice(realworld),
        "Does your faculty encourage you to ask questions and create an interactive classroom?": random.choice(agree_scale),
        
        # Teacher feedback - 25% long, 75% short
        "Please add your suggestions or concern related to any teacher.": get_feedback(
            LONG_TEACHER_FEEDBACK, SHORT_TEACHER_FEEDBACK, 0.25
        ),

        "Does your school have sufficient availability of computer or science labs and libraries that enhance your learning experience?": random.choice(agree_scale),
        "Are there sufficient resources for extracurricular activities like music, sports, yoga, dancing, art & crafts?": random.choice(extra),
        "Does your school conduct events that encourage creativity, innovation, and leadership?": random.choice(agree_scale),
        "How satisfied are you with the transportation facilities provided by school?": random.choice(transport),
        "Does your school provide career guidance and academic counselling?": random.choice(agree_scale),
        
        # School facilities feedback - 25% long, 75% short
        "Please share any suggestions or concerns about your school facilities.": get_feedback(
            LONG_SCHOOL_FEEDBACK, SHORT_SCHOOL_FEEDBACK, 0.25
        ),

        "How well does your school resolve issues of bullying and harassment?": random.choice(bullying),
        "School behaviour towards challenges like late fees or fee concessions?": random.choice(fee),
        "Do you feel that there is a fair and transparent exam results and paper checking?": random.choice(agree_scale),
        "Does your school handle academic stress and wellness issues?": random.choice(bullying),
        "Do you think your school adequately prepared you for competitive exams?": random.choice(agree_scale),
        "How satisfied are you with the overall quality of teaching at the school?": random.choice(teaching),
        "How would you recommend this school to your friends?": random.choice(["1","2","3","4","5"]),
        
        # School suggestions - 25% long, 75% short
        "Please share any suggestions or concerns about your school.": get_feedback(
            LONG_SCHOOL_SUGGESTIONS, SHORT_SCHOOL_SUGGESTIONS, 0.25
        )
    }

    data.append(row)

# Generate for DPS VARANASI (remaining 750 students)
for i in range(750):
    roll_number = generate_roll_number(20, i + 1)
    school_name = "DPS VARANASI"
    
    # Ensure uniqueness
    while (roll_number, school_name) in used_combinations:
        roll_number = generate_roll_number(20, random.randint(1, 9999))
    
    used_combinations.add((roll_number, school_name))
    
    ts = (datetime.datetime.now() - datetime.timedelta(
        minutes=random.randint(1, 600000)
    )).strftime("%d/%m/%Y %H:%M:%S")

    row = {
        "Timestamp": ts,
        "Your name": random_indian_name(),
        "Roll Number": roll_number,
        "Your school name": school_name,
        "Your class": random.choice(classes),
        "What was your last year overall percentage or CGPA?": random.randint(5, 10),
        "How much time do you spend every day on your self study and homework?": random.choice(study_time),
        "Which is your least favourite or toughest subject?": random.choice(subjects_all),
        "Subject group": random.choice(subject_groups),

        "Choose Subject Where The Subject Teacher Rating is [Excellent]": pick(2),
        "Choose Subject Where The Subject Teacher Rating is [Very Good]": pick(2),
        "Choose Subject Where The Subject Teacher Rating is [Good]": pick(2),
        "Choose Subject Where The Subject Teacher Rating is [Average]": pick(2),
        "Choose Subject Where The Subject Teacher Rating is [Poor]": pick(1),

        "Do teachers provide enough support for your academic learning and solving queries?": random.choice(agree_scale),
        "How do you meet your academic learning goal?": random.choice([
            "School only","Coaching from existing faculty","Coaching from outside faculty",
            "Online coaching","Internet materials","Reference or side books"
        ]),
        "How well do teachers give real-world applications or examples in class?": random.choice(realworld),
        "Does your faculty encourage you to ask questions and create an interactive classroom?": random.choice(agree_scale),
        
        # Teacher feedback - 25% long, 75% short
        "Please add your suggestions or concern related to any teacher.": get_feedback(
            LONG_TEACHER_FEEDBACK, SHORT_TEACHER_FEEDBACK, 0.25
        ),

        "Does your school have sufficient availability of computer or science labs and libraries that enhance your learning experience?": random.choice(agree_scale),
        "Are there sufficient resources for extracurricular activities like music, sports, yoga, dancing, art & crafts?": random.choice(extra),
        "Does your school conduct events that encourage creativity, innovation, and leadership?": random.choice(agree_scale),
        "How satisfied are you with the transportation facilities provided by school?": random.choice(transport),
        "Does your school provide career guidance and academic counselling?": random.choice(agree_scale),
        
        # School facilities feedback - 25% long, 75% short
        "Please share any suggestions or concerns about your school facilities.": get_feedback(
            LONG_SCHOOL_FEEDBACK, SHORT_SCHOOL_FEEDBACK, 0.25
        ),

        "How well does your school resolve issues of bullying and harassment?": random.choice(bullying),
        "School behaviour towards challenges like late fees or fee concessions?": random.choice(fee),
        "Do you feel that there is a fair and transparent exam results and paper checking?": random.choice(agree_scale),
        "Does your school handle academic stress and wellness issues?": random.choice(bullying),
        "Do you think your school adequately prepared you for competitive exams?": random.choice(agree_scale),
        "How satisfied are you with the overall quality of teaching at the school?": random.choice(teaching),
        "How would you recommend this school to your friends?": random.choice(["1","2","3","4","5"]),
        
        # School suggestions - 25% long, 75% short
        "Please share any suggestions or concerns about your school.": get_feedback(
            LONG_SCHOOL_SUGGESTIONS, SHORT_SCHOOL_SUGGESTIONS, 0.25
        )
    }

    data.append(row)


df = pd.DataFrame(data)
df.to_csv("school_survey_1500.csv", index=False)

# Verify uniqueness
unique_combinations = df.groupby(['Roll Number', 'Your school name']).size()
if len(unique_combinations) == ROWS:
    print("✅ All Roll Number + School Name combinations are unique")
else:
    print(f"⚠️  Warning: Found {len(unique_combinations)} unique combinations out of {ROWS}")
    duplicates = unique_combinations[unique_combinations > 1]
    if len(duplicates) > 0:
        print(f"   Duplicate combinations: {len(duplicates)}")

print(f"✅ school_survey_1500.csv generated with {ROWS} rows")
print(f"✅ JNV VARANASI students: {len(df[df['Your school name'] == 'JNV VARANASI'])}")
print(f"✅ DPS VARANASI students: {len(df[df['Your school name'] == 'DPS VARANASI'])}")
print("✅ Roll Number column added after 'Your name'")
print("✅ Roll Number format: 10XXXX (JNV), 20XXXX (DPS)")
print("✅ 25% of open-ended responses are detailed long feedback")
