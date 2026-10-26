# Seed Data for Niramaya Health AI (Auto-sync between Local and Cloud/Render)

SEED_ACCOUNTS = [
    (1, 'TestFamily', 'normaluser@example.com', '$2b$12$i0SHJEVv1b/VjdIIIGF2Ku96mujF7sN4t2AaaYZUvJf0AH0u9MwPG', '2026-09-12 13:53:42.063605', True),
    (14, 'hariyani', 'hariyani@gmail.com', '$2b$12$Mdd3Zm8sIIrGn/FoyzYVOOrl42VFVx6nDdlJegFvLqn5R6hfWVboG', '2026-10-22 12:31:47.703434', True),
    (15, 'bhagvat', 'hariyanibhagvat@gmail.com', '$2b$12$D4LnERx3TnZ6cgEVk93ZVuZnAIStxkEakM08JY2piacz1KNHOdPU2', '2026-10-22 23:16:25.466025', True),
    (18, 'mrunali', 'mrunali@niramaya.com', '$2b$12$svpSxVIQbgvZkoNLlx2qFO6ggnaIezv1aDeXsS6GncA8Dus3E8NLG', '2026-10-23 13:47:21.171546', True),
    (22, 'SharmaFamily', 'student_test@niramaya.com', '$2b$12$Cu3rIwXn2WWM3whh3WvSgu9Gpyv4hxCzCZ5lJqmXCnQEt.PzyuNYm', '2026-10-26 13:44:49.835800', True),
    (23, 'PatelFamily', 'testuser_1793002659@niramaya.com', '$2b$12$mHYC/YqDmBnZ3iJJ831wIeAdfsJxRwHrWNQH7Frh2/y4tUoyzUZJ.', '2026-10-26 13:47:40.325441', True),
    (24, 'vatsal', 'vatsal@gmail.com', '$2b$12$ICiKkfYhOgcg2WOgE9E4beFjRSDXEojl4XbXZh7BHEdZgZC6PYHMa', '2026-10-26 14:41:06.116783', True),
    (25, 'paresh', 'phariyani@gmail.com', '$2b$12$EVcHti39X.Y.D/GblspXzufF7dIkYPfo9qX9.8XnRI9GeouKaF4sm', '2026-10-26 14:47:14.045229', True),
    (26, 'SharmaFamily', 'onemember_1793006694@niramaya.com', '$2b$12$CWg2Zd7jGI.T.XSGLpPcA.3bElmLiuHc0qWteORBv/Yz7YY6Lq3U.', '2026-10-26 14:54:55.128186', True),
    (27, 'VermaFamily', 'finaltest_1793006827@niramaya.com', '$2b$12$IEOSPSdA0MJ3Cp0lEzG4uulnlQimsKaKKIJVYef34fWsh0.MWvxim', '2026-10-26 14:57:08.174825', True),
    (36, 'UpdatedSmithFamily', 'updatedsmith@example.com', '$2b$12$A6f5gAjEOljEkoYNGTmJPOPOCEl9zW6hXZH6pyjScojLl5PY6aVRG', '2026-10-26 17:46:00.785576', True),
]

SEED_MEMBERS = [
    (8, 14, 'bhagvat', 'Male', 22, '53', '50', '2026-10-22 12:32:13.896274'),
    (14, 18, 'mrunali goyani', 'Female', 22, '5', '60', '2026-10-23 22:25:57.331688'),
    (16, 18, 'bhagvat', 'Male', 22, '53', '50', '2026-10-26 12:54:20.673753'),
    (17, 22, 'SharmaFamily', 'Other', 25, '170', '65', '2026-10-26 13:44:49.835800'),
    (18, 23, 'PatelFamily', 'Other', 25, '170', '65', '2026-10-26 13:47:40.325441'),
    (23, 27, 'Amit Verma', 'Male', 24, 'N/A', 'N/A', '2026-10-26 14:57:08.234643'),
    (24, 1, 'TestFamily', 'Other', 25, '170', '65', '2026-10-26 17:08:27.243157'),
    (29, 36, 'John Smith', 'Male', 35, '175', '70', '2026-10-26 17:46:00.787729'),
]

SEED_CHATS = [
    (6, 18, 14, 'covid19', "**Medical Overview for 'covid19':**\n- Always monitor your symptoms closely including duration and severity.\n- Common health guidance includes staying hydrated, eating balanced meals, and getting sufficient rest.\n- If you are experiencing sudden severe pain, high fever, or difficulty breathing, seek urgent medical care.\n- *Disclaimer:* Niramaya is an informational health assistant and does not replace official medical advice.", 'BioGPT', '2026-10-23 22:26:57.170861'),
    (7, 18, 14, 'covid19', '**Health Information regarding:** covid19\n\n- **Primary Guidance:** Monitor your temperature, stay adequately hydrated, and rest.\n- **When to see a doctor:** If symptoms persist longer than 48 hours, worsen rapidly, or cause acute distress.\n- **General Care:** Avoid self-medicating without proper clinical supervision.\n\n*(Disclaimer: Niramaya provides AI-driven informational insights and does not substitute for certified doctor care.)*', 'Gemini', '2026-10-23 22:27:28.730774'),
    (8, 18, 14, 'covid19', '{"Description":"No known symptoms recognized from \\"covid19\\". Please try common symptoms such as: abdominal cramp, abdominal distention, abnormal behavior, abnormal bleeding, abnormal sensation, abnormally frequent, abscess, aching.","predicted_disease":"No exact match found"}', 'LRv1', '2026-10-23 22:27:46.666388'),
    (10, 23, 18, 'headache, fatigue', 'Rest and stay hydrated.', 'LRv1', '2026-10-26 13:47:44.476517'),
    (11, 18, 16, 'covid19', "**Condition / Topic:** COVID-19\n\n**Medical Overview:**\nCoronavirus disease 2019 (COVID-19) is a contagious disease caused by the coronavirus SARS-CoV-2. Starting in January 2020, the disease spread worldwide, resulting in the COVID-19 pandemic. In March 2020, the World Health Organization declared COVID-19 a global health emergency; they declared the end of the emergency on 5 May 2023.\n\n**Key Health Precautions & Self-Care:**\n- Rest adequately and stay well-hydrated with warm liquids\n- Isolate in a well-ventilated space to prevent spreading infection\n- Monitor body temperature and blood oxygen saturation (SpO2)\n- Wear a protective mask and practice frequent handwashing\n\n**When to Seek Immediate Medical Attention:**\n- High persistent fever that doesn't reduce with medication\n- Shortness of breath, chest tightness, or severe dizziness\n- Uncontrolled vomiting, acute localized pain, or dehydration\n\n*(Disclaimer: Niramaya provides AI-guided health insights. This does not replace formal clinical diagnosis or physician consultation.)*", 'BioGPT', '2026-10-26 14:39:38.502365'),
]

SEED_HEALTH_CONTENT = [
    (1, 'wellness_tip', 'Spring Seasonal Wellness', 'Spring', 'Eat fresh greens, berries, and lean proteins to boost energy. Avoid heavy, oily foods that can cause sluggishness. Stay active with outdoor hikes or cycling.', 'Niramaya Health Editorial Team', None, None, 'published', '2026-09-12 14:00:09.788412', '2026-09-12 14:00:09.788412'),
    (2, 'wellness_tip', 'Summer Hydration & Energy', 'Summer', 'Eat hydrating fruits like watermelon and light salads. Avoid excessive caffeine and sugary drinks that dehydrate. Stay active by swimming or jogging early to beat the heat.', 'Niramaya Health Editorial Team', None, None, 'published', '2026-09-12 14:00:09.788412', '2026-09-12 14:00:09.788412'),
    (3, 'wellness_tip', 'Autumn Warmth & Active Care', 'Autumn', 'Eat root vegetables, apples, and warm soups for comfort. Avoid processed snacks and excess sugar. Stay active with indoor yoga or pilates as the days cool down.', 'Niramaya Health Editorial Team', None, None, 'published', '2026-09-12 14:00:09.788412', '2026-09-12 14:00:09.788412'),
    (4, 'wellness_tip', 'Winter Vitality & Defense', 'Winter', 'Eat hearty stews, citrus fruits, and whole grains for warmth. Avoid high-fat comfort foods and excessive alcohol. Stay active with indoor workouts or winter sports.', 'Niramaya Health Editorial Team', None, None, 'published', '2026-09-12 14:00:09.788412', '2026-09-12 14:00:09.788412'),
    (5, 'article', 'Artificial Intelligence in Early Health Screening', 'AI Health', 'Recent studies highlight the transformative potential of machine learning and natural language processing in assisting early symptom analysis and preventative wellness monitoring.', 'Europe PMC / Niramaya Research', None, None, 'published', '2026-09-12 14:00:09.788412', '2026-09-12 14:00:09.788412'),
    (6, 'wellness_tip', 'Updated Monsoon Wellness Guide', 'Monsoon', 'Drink warm herbal tea and eat fresh immunity-boosting foods.', 'Niramaya Senior Health Team', '', '', 'archived', '2026-09-12 14:02:35.176542', '2026-09-12 14:02:36.083650'),
    (7, 'article', 'Machine Learning in Preventative Medicine', 'AI Health', 'Explores how ML algorithms predict early disease markers.', 'Niramaya AI Labs', '', '', 'draft', '2026-09-12 14:02:35.247814', '2026-09-12 14:02:35.247814'),
    (9, 'wellness_tip', 'Updated Monsoon Wellness Guide', 'Monsoon', 'Drink warm herbal tea and eat fresh immunity-boosting foods.', 'Niramaya Senior Health Team', '', '', 'archived', '2026-09-12 14:03:17.653197', '2026-09-12 14:03:18.474009'),
    (10, 'article', 'Machine Learning in Preventative Medicine', 'AI Health', 'Explores how ML algorithms predict early disease markers.', 'Niramaya AI Labs', '', '', 'draft', '2026-09-12 14:03:17.840616', '2026-09-12 14:03:17.840616'),
    (12, 'wellness_tip', 'Updated Monsoon Wellness Guide', 'Monsoon', 'Drink warm herbal tea and eat fresh immunity-boosting foods.', 'Niramaya Senior Health Team', '', '', 'archived', '2026-09-12 14:07:16.787654', '2026-09-12 14:07:17.678842'),
    (13, 'article', 'Machine Learning in Preventative Medicine', 'AI Health', 'Explores how ML algorithms predict early disease markers.', 'Niramaya AI Labs', '', '', 'draft', '2026-09-12 14:07:16.962033', '2026-09-12 14:07:16.962033'),
    (15, 'wellness_tip', 'Updated Monsoon Wellness Guide', 'Monsoon', 'Drink warm herbal tea and eat fresh immunity-boosting foods.', 'Niramaya Senior Health Team', '', '', 'archived', '2026-09-12 14:10:46.356974', '2026-09-12 14:10:47.454090'),
    (16, 'article', 'Machine Learning in Preventative Medicine', 'AI Health', 'Explores how ML algorithms predict early disease markers.', 'Niramaya AI Labs', '', '', 'draft', '2026-09-12 14:10:46.429793', '2026-09-12 14:10:46.429793'),
    (18, 'wellness_tip', 'Updated Monsoon Wellness Guide', 'Monsoon', 'Drink warm herbal tea and eat fresh immunity-boosting foods.', 'Niramaya Senior Health Team', '', '', 'archived', '2026-10-23 12:24:21.487350', '2026-10-23 12:24:22.873302'),
    (19, 'article', 'Machine Learning in Preventative Medicine', 'AI Health', 'Explores how ML algorithms predict early disease markers.', 'Niramaya AI Labs', '', '', 'draft', '2026-10-23 12:24:21.678702', '2026-10-23 12:24:21.678702'),
    (21, 'wellness_tip', 'Updated Monsoon Wellness Guide', 'Monsoon', 'Drink warm herbal tea and eat fresh immunity-boosting foods.', 'Niramaya Senior Health Team', '', '', 'archived', '2026-10-24 09:29:47.694577', '2026-10-24 09:29:48.791803'),
    (22, 'article', 'Machine Learning in Preventative Medicine', 'AI Health', 'Explores how ML algorithms predict early disease markers.', 'Niramaya AI Labs', '', '', 'draft', '2026-10-24 09:29:47.855737', '2026-10-24 09:29:47.855737'),
    (24, 'wellness_tip', 'Updated Monsoon Wellness Guide', 'Monsoon', 'Drink warm herbal tea and eat fresh immunity-boosting foods.', 'Niramaya Senior Health Team', '', '', 'archived', '2026-10-26 17:09:59.410880', '2026-10-26 17:10:00.129712'),
    (25, 'article', 'Machine Learning in Preventative Medicine', 'AI Health', 'Explores how ML algorithms predict early disease markers.', 'Niramaya AI Labs', '', '', 'draft', '2026-10-26 17:09:59.489233', '2026-10-26 17:09:59.489233'),
    (27, 'wellness_tip', 'Updated Monsoon Wellness Guide', 'Monsoon', 'Drink warm herbal tea and eat fresh immunity-boosting foods.', 'Niramaya Senior Health Team', '', '', 'archived', '2026-10-26 17:18:35.310735', '2026-10-26 17:18:36.417116'),
    (28, 'article', 'Machine Learning in Preventative Medicine', 'AI Health', 'Explores how ML algorithms predict early disease markers.', 'Niramaya AI Labs', '', '', 'draft', '2026-10-26 17:18:35.499688', '2026-10-26 17:18:35.499688'),
    (30, 'wellness_tip', 'Updated Monsoon Wellness Guide', 'Monsoon', 'Drink warm herbal tea and eat fresh immunity-boosting foods.', 'Niramaya Senior Health Team', '', '', 'archived', '2026-10-26 17:33:46.318551', '2026-10-26 17:33:47.440145'),
    (31, 'article', 'Machine Learning in Preventative Medicine', 'AI Health', 'Explores how ML algorithms predict early disease markers.', 'Niramaya AI Labs', '', '', 'draft', '2026-10-26 17:33:46.500083', '2026-10-26 17:33:46.500083'),
    (33, 'wellness_tip', 'Updated Monsoon Wellness Guide', 'Monsoon', 'Drink warm herbal tea and eat fresh immunity-boosting foods.', 'Niramaya Senior Health Team', '', '', 'archived', '2026-10-26 17:46:03.942563', '2026-10-26 17:46:04.986826'),
    (34, 'article', 'Machine Learning in Preventative Medicine', 'AI Health', 'Explores how ML algorithms predict early disease markers.', 'Niramaya AI Labs', '', '', 'draft', '2026-10-26 17:46:04.262867', '2026-10-26 17:46:04.262867'),
]
