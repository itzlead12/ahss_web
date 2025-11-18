// Mock Data
const mockData = {
    schools: [
        {
            id: 1,
            name: "Addis Ababa High School",
            description: "Leading robotics and coding programs with state-of-the-art laboratories.",
            student_count: 200,
            club_count: 5,
            icon: "bi-building",
            status: "active"
        },
        {
            id: 2,
            name: "Ethiopian Science Academy",
            description: "Specialized in environmental science and astronomy with advanced research facilities.",
            student_count: 150,
            club_count: 4,
            icon: "bi-building",
            status: "active"
        },
        {
            id: 3,
            name: "Future Leaders STEM School",
            description: "Focused on electronics and engineering with hands-on project-based learning.",
            student_count: 180,
            club_count: 6,
            icon: "bi-building",
            status: "active"
        }
    ],
    events: [
        {
            id: 1,
            title: "Science Fair 2024",
            description: "Annual science fair showcasing student projects from all clubs.",
            event_date: "2024-10-15",
            event_type: "fair",
            status: "upcoming",
            registration_link: "/register/science-fair",
            gallery_link: ""
        },
        {
            id: 2,
            title: "Ethio-Hackathon",
            description: "48-hour coding competition focusing on developing tech solutions.",
            event_date: "2024-11-05",
            event_type: "competition",
            status: "upcoming",
            registration_link: "/register/hackathon",
            gallery_link: ""
        },
        {
            id: 3,
            title: "Robotics Competition 2024",
            description: "Inter-school robotics competition featuring autonomous robots.",
            event_date: "2024-06-20",
            event_type: "competition",
            status: "completed",
            registration_link: "",
            gallery_link: "/gallery/robotics-2024"
        }
    ],
    team: [
        {
            id: 1,
            name: "Samuel Bekele",
            role: "Society President",
            description: "Leads the overall direction of the society and represents us in external events.",
            image: "/static/img/team/president.webp",
            status: "active"
        },
        {
            id: 2,
            name: "Liya Tadesse",
            role: "Vice President",
            description: "Coordinates between clubs and ensures smooth operation of all activities.",
            image: "/static/img/team/vice-president.webp",
            status: "active"
        },
        {
            id: 3,
            name: "Daniel Haile",
            role: "Robotics Club Coordinator",
            description: "Leads the robotics club activities, competitions, and project development.",
            image: "/static/img/team/robotics-coordinator.webp",
            status: "active"
        }
    ],
    messages: [
        {
            id: 1,
            name: "Meron Tesfaye",
            email: "meron.tesfaye@email.com",
            message: "I'm interested in joining the robotics club. What are the requirements?",
            date: "2024-01-15"
        },
        {
            id: 2,
            name: "Abel Getachew",
            email: "abel.getachew@email.com",
            message: "Can you provide more information about the upcoming hackathon?",
            date: "2024-01-14"
        },
        {
            id: 3,
            name: "Hana Mohammed",
            email: "hana.mohammed@email.com",
            message: "I'd like to volunteer as a mentor for the coding club.",
            date: "2024-01-13"
        }
    ]
};

// Initialize Dashboard
document.addEventListener('DOMContentLoaded', function() {
    initializeDashboard();
    loadNavigation();
    loadSchools();
    loadEvents();
    loadTeam();
    loadMessages();
});

// Navigation Management
function loadNavigation() {
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove active class from all links
            navLinks.forEach(nl => nl.classList.remove('active'));
            
            // Add active class to clicked link
            this.classList.add('active');
            
            // Show corresponding section
            const targetId = this.getAttribute('href').substring(1);
            showSection(targetId);
        });
    });
}

function showSection(sectionId) {
    // Hide all sections
    const sections = document.querySelectorAll('.management-section, .dashboard-section');
    sections.forEach(section => {
        section.style.display = 'none';
    });
    
    // Show target section
    const targetSection = document.getElementById(sectionId);
    if (targetSection) {
        targetSection.style.display = 'block';
    }
}

// Schools Management
function loadSchools() {
    const tbody = document.getElementById('schools-table-body');
    tbody.innerHTML = '';
    
    mockData.schools.forEach(school => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <strong>${school.name}</strong>
                <br><small class="text-muted">${school.description.substring(0, 60)}...</small>
            </td>
            <td>${school.student_count}+</td>
            <td>${school.club_count}</td>
            <td><span class="status-badge status-${school.status}">${school.status}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-primary btn-action" onclick="editSchool(${school.id})">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-action" onclick="deleteSchool(${school.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function addSchool() {
    const form = document.getElementById('addSchoolForm');
    const formData = new FormData(form);
    
    const newSchool = {
        id: mockData.schools.length + 1,
        name: formData.get('name'),
        description: formData.get('description'),
        student_count: parseInt(formData.get('student_count')),
        club_count: parseInt(formData.get('club_count')),
        icon: formData.get('icon'),
        status: 'active'
    };
    
    mockData.schools.push(newSchool);
    loadSchools();
    updateStats();
    
    // Close modal and reset form
    bootstrap.Modal.getInstance(document.getElementById('addSchoolModal')).hide();
    form.reset();
    
    showAlert('School added successfully!', 'success');
}

function editSchool(id) {
    const school = mockData.schools.find(s => s.id === id);
    if (school) {
        // In a real app, you'd populate a modal with school data
        showAlert(`Editing school: ${school.name}`, 'info');
    }
}

function deleteSchool(id) {
    if (confirm('Are you sure you want to delete this school?')) {
        mockData.schools = mockData.schools.filter(s => s.id !== id);
        loadSchools();
        updateStats();
        showAlert('School deleted successfully!', 'success');
    }
}

// Events Management
function loadEvents() {
    const tbody = document.getElementById('events-table-body');
    tbody.innerHTML = '';
    
    mockData.events.forEach(event => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <strong>${event.title}</strong>
                <br><small class="text-muted">${event.description.substring(0, 60)}...</small>
            </td>
            <td>${formatDate(event.event_date)}</td>
            <td>${event.event_type}</td>
            <td><span class="status-badge status-${event.status}">${event.status}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-primary btn-action" onclick="editEvent(${event.id})">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-action" onclick="deleteEvent(${event.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function addEvent() {
    const form = document.getElementById('addEventForm');
    const formData = new FormData(form);
    
    const newEvent = {
        id: mockData.events.length + 1,
        title: formData.get('title'),
        description: formData.get('description'),
        event_date: formData.get('event_date'),
        event_type: formData.get('event_type'),
        status: formData.get('status'),
        registration_link: formData.get('registration_link'),
        gallery_link: formData.get('gallery_link')
    };
    
    mockData.events.push(newEvent);
    loadEvents();
    updateStats();
    
    // Close modal and reset form
    bootstrap.Modal.getInstance(document.getElementById('addEventModal')).hide();
    form.reset();
    
    showAlert('Event added successfully!', 'success');
}

function editEvent(id) {
    const event = mockData.events.find(e => e.id === id);
    if (event) {
        showAlert(`Editing event: ${event.title}`, 'info');
    }
}

function deleteEvent(id) {
    if (confirm('Are you sure you want to delete this event?')) {
        mockData.events = mockData.events.filter(e => e.id !== id);
        loadEvents();
        updateStats();
        showAlert('Event deleted successfully!', 'success');
    }
}

// Team Management
function loadTeam() {
    const tbody = document.getElementById('team-table-body');
    tbody.innerHTML = '';
    
    mockData.team.forEach(member => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>
                <strong>${member.name}</strong>
                <br><small class="text-muted">${member.description.substring(0, 60)}...</small>
            </td>
            <td>${member.role}</td>
            <td><span class="status-badge status-${member.status}">${member.status}</span></td>
            <td>
                <button class="btn btn-sm btn-outline-primary btn-action" onclick="editTeamMember(${member.id})">
                    <i class="bi bi-pencil"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-action" onclick="deleteTeamMember(${member.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function addTeamMember() {
    const form = document.getElementById('addTeamForm');
    const formData = new FormData(form);
    
    const newMember = {
        id: mockData.team.length + 1,
        name: formData.get('name'),
        role: formData.get('role'),
        description: formData.get('description'),
        image: formData.get('image'),
        status: 'active'
    };
    
    mockData.team.push(newMember);
    loadTeam();
    updateStats();
    
    // Close modal and reset form
    bootstrap.Modal.getInstance(document.getElementById('addTeamModal')).hide();
    form.reset();
    
    showAlert('Team member added successfully!', 'success');
}

function editTeamMember(id) {
    const member = mockData.team.find(m => m.id === id);
    if (member) {
        showAlert(`Editing team member: ${member.name}`, 'info');
    }
}

function deleteTeamMember(id) {
    if (confirm('Are you sure you want to delete this team member?')) {
        mockData.team = mockData.team.filter(m => m.id !== id);
        loadTeam();
        updateStats();
        showAlert('Team member deleted successfully!', 'success');
    }
}

// Messages Management
function loadMessages() {
    const tbody = document.getElementById('messages-table-body');
    tbody.innerHTML = '';
    
    mockData.messages.forEach(message => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${message.name}</td>
            <td>${message.email}</td>
            <td>${message.message.substring(0, 80)}...</td>
            <td>${formatDate(message.date)}</td>
            <td>
                <button class="btn btn-sm btn-outline-primary btn-action" onclick="viewMessage(${message.id})">
                    <i class="bi bi-eye"></i>
                </button>
                <button class="btn btn-sm btn-outline-danger btn-action" onclick="deleteMessage(${message.id})">
                    <i class="bi bi-trash"></i>
                </button>
            </td>
        `;
        tbody.appendChild(row);
    });
}

function viewMessage(id) {
    const message = mockData.messages.find(m => m.id === id);
    if (message) {
        alert(`Message from ${message.name} (${message.email}):\n\n${message.message}`);
    }
}

function deleteMessage(id) {
    if (confirm('Are you sure you want to delete this message?')) {
        mockData.messages = mockData.messages.filter(m => m.id !== id);
        loadMessages();
        updateStats();
        showAlert('Message deleted successfully!', 'success');
    }
}

// Utility Functions
function initializeDashboard() {
    updateStats();
}

function updateStats() {
    document.getElementById('schools-count').textContent = mockData.schools.length;
    document.getElementById('events-count').textContent = mockData.events.length;
    document.getElementById('team-count').textContent = mockData.team.length;
    document.getElementById('messages-count').textContent = mockData.messages.length;
}

function formatDate(dateString) {
    const options = { year: 'numeric', month: 'short', day: 'numeric' };
    return new Date(dateString).toLocaleDateString(undefined, options);
}

function showAlert(message, type) {
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
    alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    // Add to page
    const main = document.querySelector('main');
    main.insertBefore(alertDiv, main.firstChild);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (alertDiv.parentNode) {
            alertDiv.remove();
        }
    }, 5000);
}