function toggleCommands() {
    const commandsSection = document.getElementById('commands-section');
    const toggleBtn = document.getElementById('toggle-commands-btn');

    if (commandsSection.style.display === 'none' || commandsSection.style.display === '') {
        commandsSection.style.display = 'block';
        toggleBtn.textContent = 'Hide Commands';
        // Smooth scroll to commands
        commandsSection.scrollIntoView({ behavior: 'smooth' });
    } else {
        commandsSection.style.display = 'none';
        toggleBtn.textContent = 'Commands';
    }
}
