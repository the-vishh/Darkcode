const mentors = [
  { name: 'Birmohan Singh', rating: '5', techStack: ['JavaScript', 'HTML', 'CSS'] },
  { name: 'Damanpreet Singh', rating: '4.5', techStack: ['Python', 'Machine Learning'] },
  { name: 'Singh Goraya', rating: '5.0', techStack: ['React', 'HTML', 'NodeJS'] },
  { name: 'Manoj Sachan', rating: '5.0', techStack: ['Frontend', 'Javascript', 'Typescript'] },
  { name: 'Gurjinder Kaur', rating: '5.0', techStack: ['Generative AI', 'React', 'Scrum'] },
  { name: 'Amar Nath', rating: '4.9', techStack: ['Data Engineering', 'AWS', 'Data Analytics'] },
  { name: 'Jagdeep Singh', rating: '5.0', techStack: ['Product Design', 'User Interface Design', 'UX/UI Design']},
  { name: 'Manminder Singh', rating: '5.0', techStack: ['Azure, Cloud', 'Google Cloud']},
  { name: 'Preetpal Kaur', rating: '4.8', techStack: ['Engineering', 'Interview', 'Interview prep']},
  { name: 'Tajinder Singh', rating: '5.0', techStack: ['Deep Learning', 'Computer Vision', 'Python']},
  { name: 'Utkarsh', rating: '5.0', techStack: ['UX Design', 'AI Ethics', 'Design Leadership']},
  { name: 'Vinod Kumar', rating: '5.0', techStack: ['Interview Preparation', 'Resume Review', 'Salary Negotiation']},
  { name: 'Jaspal Singh', rating: '5.0', techStack: ['Software Engineering', 'Data Structures', 'Java']},
  { name: 'Rahul Gautam', rating: '5.0', techStack: ['Marketing Strategy', 'Market, Startup']},
      { name: 'Sukhpreet Singh', rating: '5.0', techStack: ['Product', 'Marketplace', 'Entrepreneurship']},
  { name: 'Vikash Kumar', rating: '5.0', techStack: ['Machine learning', 'Natural Language Processing', 'Computer Vision']},
];

const mentorList = document.querySelector('.mentor-list');

mentors.forEach(mentor => {
  const mentorCard = document.createElement('div');
  mentorCard.classList.add('mentor-card');

  const techStackHTML = mentor.techStack.map(tech => `<span class="tech-badge">${tech}</span>`).join('');

  mentorCard.innerHTML = `
      <div class="mentor-details">
          <div class="mentor-header">
              <h3>${mentor.name}</h3>
              <div class="mentor-rating">
                  <span class="rating-icon">★</span>
                  <span>${mentor.rating}</span>
              </div>
          </div>
          <div class="mentor-techstack">
              ${techStackHTML}
          </div>
      </div>
  `;

  mentorList.appendChild(mentorCard);
});