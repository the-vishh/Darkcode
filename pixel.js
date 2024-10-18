const bookedSlots = [];


function bookSession(mentor) {
  if (bookedSlots.includes(mentor)) {
    alert(`${mentor} is already booked!`);
  } else {
    bookedSlots.push(mentor);
    document.getElementById('confirmation-text').innerText = `${mentor} session booked!`;
    document.getElementById('confirmation-modal').style.display = 'block';
    
    // Update booking status
    const mentorElements = document.querySelectorAll('.mentor');
    mentorElements.forEach((mentorElement) => {
      if (mentorElement.querySelector('h3').innerText === mentor) {
        mentorElement.querySelector('.status').classList.remove('available');
        mentorElement.querySelector('.status').classList.add('booked');
        mentorElement.querySelector('.status').innerText = 'Booked';
      }
    });
  }
}

// Function to close the confirmation modal
function closeModal() {
  document.getElementById('confirmation-modal').style.display = 'none';
}
