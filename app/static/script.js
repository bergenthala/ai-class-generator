// Game state
let gameState = {
    playerId: null,
    playerClass: null,
    storyProgress: 0,
    initialized: false
};

const API_BASE = window.location.origin;

// Initialize game
function initGame() {
    // Generate unique player ID
    gameState.playerId = `player_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    document.getElementById('player-name').textContent = `Player ${gameState.playerId.slice(-6)}`;
    
    // Show class selection
    showClassSelection();
}

// Show class selection
function showClassSelection() {
    document.getElementById('class-selection').style.display = 'block';
    document.getElementById('action-buttons').style.display = 'none';
    document.getElementById('text-input').style.display = 'none';
    
    // Add event listeners to class buttons
    document.querySelectorAll('.class-btn').forEach(btn => {
        btn.addEventListener('click', () => selectClass(btn.dataset.class));
    });
}

// Select initial class
async function selectClass(className) {
    gameState.playerClass = className;
    const classNames = {
        warrior: 'Warrior',
        priest: 'Priest',
        mage: 'Mage',
        thief: 'Thief',
        wanderer: 'Wanderer'
    };
    
    document.getElementById('player-class').textContent = classNames[className];
    document.getElementById('class-selection').style.display = 'none';
    
    // Add welcome message
    addMessage('system', `You have chosen the path of the ${classNames[className]}!`);
    
    // Start story based on class
    await startStory(className);
}

// Start the story
async function startStory(className) {
    // Try to generate AI story, fallback to hardcoded
    try {
        const response = await fetch(`${API_BASE}/generate-story`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                context: `Starting a new adventure as a ${className}`,
                player_class: className,
                player_id: gameState.playerId
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            const storyText = data.story_text;
            // Display as single message for natural flow
            await delay(1000);
            addMessage('bot', storyText);
        } else {
            throw new Error('AI generation failed');
        }
    } catch (error) {
        // Fallback to hardcoded stories
        const stories = {
            warrior: "You stand at the gates of the training grounds, your sword gleaming in the sunlight. The master trainer approaches with a knowing smile: 'Prove your worth, warrior. Your journey begins with combat, but remember - true strength comes from within.'",
            priest: "You enter the sacred temple, bathed in ethereal light that seems to emanate from the very stones. The high priest greets you with open arms: 'Welcome, child of light. Knowledge and wisdom await those who seek truth.'",
            mage: "You step into the arcane library, where ancient tomes float through the air like living creatures. The archmage materializes before you: 'Magic flows through knowledge, young apprentice. Study well, for the path of the arcane is both wondrous and perilous.'",
            thief: "You slip into the shadows of the city, moving like a ghost through the narrow alleys. A voice whispers from the darkness: 'Stealth and cunning are your tools. Use them wisely, for the shadows hold both opportunity and danger.'",
            wanderer: "You walk an untrodden path, free from the constraints of tradition. A mysterious figure appears at a crossroads: 'You walk alone, but that is your strength. Forge your own destiny, for the world rewards those bold enough to choose their own way.'"
        };
        
        const story = stories[className] || stories.wanderer;
        await delay(1000);
        addMessage('bot', story);
    }
    
    await delay(1000);
    addMessage('bot', "What would you like to do?");
    showActionButtons();
    gameState.initialized = true;
}

// Show action buttons
function showActionButtons() {
    document.getElementById('action-buttons').style.display = 'grid';
    document.getElementById('text-input').style.display = 'none';
    
    // Add event listeners
    document.querySelectorAll('.action-btn').forEach(btn => {
        btn.onclick = () => handleAction(btn.dataset.action);
    });
}

// Handle action
async function handleAction(action) {
    const actionMessages = {
        read_book: {
            message: "You sit down and open a book, absorbing its knowledge...",
            event: { event_name: "read_book", metadata: { book_id: `book_${Date.now()}`, length_pages: Math.floor(Math.random() * 500) + 100 } }
        },
        kill_monster: {
            message: "You draw your weapon and engage in combat!",
            event: { event_name: "kill_monster", metadata: { monster_id: `monster_${Date.now()}`, type: "goblin" } }
        },
        craft_item: {
            message: "You gather materials and begin crafting...",
            event: { event_name: "craft_item", metadata: { crafted_item_id: `item_${Date.now()}`, type: "weapon" } }
        },
        explore: {
            message: "You venture into the unknown, discovering new places...",
            event: { event_name: "explore", metadata: { location_id: `loc_${Date.now()}` } }
        },
        meditate: {
            message: "You find a quiet place and enter deep meditation...",
            event: { event_name: "meditate", metadata: { duration: Math.floor(Math.random() * 60) + 10 } }
        }
    };
    
    const actionData = actionMessages[action];
    if (!actionData) return;
    
    addMessage('user', actionData.message);
    
    // Send event to backend
    try {
        const response = await fetch(`${API_BASE}/events`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                user_id: gameState.playerId,
                ...actionData.event
            })
        });
        
        if (response.ok) {
            const eventData = await response.json();
            console.log('Event recorded:', eventData);
            
            // Small delay to ensure backend has processed the event
            await delay(500);
            
            // Update stats (with retry logic)
            let statsUpdated = false;
            for (let i = 0; i < 3; i++) {
                await updateStats();
                // Check if stats were actually updated by checking the response
                await delay(200);
                if (i < 2) {
                    // Try again if this isn't the last attempt
                    await delay(300);
                }
            }
            
            // Check for new classes
            await checkForNewClasses();
            
            // Add story continuation
            await continueStory(action);
        } else {
            addMessage('system', "Error: Could not record your action.");
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('system', "Error: Could not connect to the server.");
    }
}

// Continue story based on action
async function continueStory(action) {
    // Try to generate AI story continuation
    try {
        const response = await fetch(`${API_BASE}/generate-story`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                context: `The player just performed the action: ${action}`,
                player_class: gameState.playerClass,
                action: action,
                player_id: gameState.playerId
            })
        });
        
        if (response.ok) {
            const data = await response.json();
            const storyText = data.story_text;
            
            // Display the story text as a single message (more natural)
            await delay(500);
            addMessage('bot', storyText);
            return;
        } else {
            console.log('AI generation failed with status:', response.status);
        }
    } catch (error) {
        console.log('AI generation failed, using fallback:', error);
    }
    
    // Fallback to single message for better flow
    const continuations = {
        read_book: "The knowledge flows into your mind like a gentle stream, expanding your understanding of the world. You feel wiser, more connected to the mysteries that surround you.",
        kill_monster: "The battle is won! Your combat prowess grows with each victory, and you feel the thrill of triumph coursing through your veins. More challenges await on the horizon.",
        craft_item: "Your creation is complete! A fine piece of work that showcases your skill and dedication. The item gleams with potential, ready to serve you well.",
        explore: "You discover new paths and hidden secrets in the world around you. Each step reveals something unexpected, reminding you that adventure lies around every corner.",
        meditate: "You feel more centered and focused after your meditation. Inner peace brings clarity, and you sense a deeper connection to the world around you."
    };
    
    const line = continuations[action] || "You continue your journey, ready for whatever comes next.";
    await delay(800);
    addMessage('bot', line);
}

// Update stats
async function updateStats() {
    try {
        console.log('Fetching stats for player:', gameState.playerId);
        const response = await fetch(`${API_BASE}/player/${gameState.playerId}/features`);
        
        if (response.ok) {
            const data = await response.json();
            console.log('Received stats data:', data);
            
            const counts = data.event_counts || {};
            console.log('Event counts:', counts);
            
            // Update each stat, ensuring we get the latest values
            const booksCount = counts.read_book?.count || 0;
            const monstersCount = counts.kill_monster?.count || 0;
            const craftedCount = counts.craft_item?.distinct_count || 0;
            
            console.log('Parsed counts:', { booksCount, monstersCount, craftedCount });
            
            // Update the DOM elements directly
            const booksEl = document.getElementById('stat-books');
            const monstersEl = document.getElementById('stat-monsters');
            const craftedEl = document.getElementById('stat-crafted');
            
            console.log('DOM elements found:', {
                booksEl: !!booksEl,
                monstersEl: !!monstersEl,
                craftedEl: !!craftedEl
            });
            
            if (booksEl) {
                console.log('Updating books from', booksEl.textContent, 'to', booksCount);
                booksEl.textContent = booksCount;
                booksEl.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    booksEl.style.transform = 'scale(1)';
                }, 200);
            } else {
                console.error('stat-books element not found!');
            }
            
            if (monstersEl) {
                console.log('Updating monsters from', monstersEl.textContent, 'to', monstersCount);
                monstersEl.textContent = monstersCount;
                monstersEl.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    monstersEl.style.transform = 'scale(1)';
                }, 200);
            } else {
                console.error('stat-monsters element not found!');
            }
            
            if (craftedEl) {
                console.log('Updating crafted from', craftedEl.textContent, 'to', craftedCount);
                craftedEl.textContent = craftedCount;
                craftedEl.style.transform = 'scale(1.1)';
                setTimeout(() => {
                    craftedEl.style.transform = 'scale(1)';
                }, 200);
            } else {
                console.error('stat-crafted element not found!');
            }
            
            console.log('Stats update complete');
        } else {
            const errorText = await response.text();
            console.error('Failed to fetch stats:', response.status, errorText);
        }
    } catch (error) {
        console.error('Error updating stats:', error);
    }
}

// Check for new classes
async function checkForNewClasses() {
    try {
        // Manually trigger unlock check
        await fetch(`${API_BASE}/check-unlocks/${gameState.playerId}`, {
            method: 'POST'
        });
        
        // Get updated classes
        const response = await fetch(`${API_BASE}/player/${gameState.playerId}/classes`);
        if (response.ok) {
            const classes = await response.json();
            document.getElementById('stat-classes').textContent = classes.length;
            displayClasses(classes);
            
            // Announce new classes
            if (classes.length > 0) {
                const latestClass = classes[classes.length - 1];
                await delay(1000);
                addMessage('system', `🎉 NEW CLASS UNLOCKED: ${latestClass.class_data.name} (${latestClass.class_data.rarity})!`);
                await delay(1000);
                addMessage('bot', latestClass.class_data.description);
            }
        }
    } catch (error) {
        console.error('Error checking classes:', error);
    }
}

// Display classes
function displayClasses(classes) {
    const container = document.getElementById('classes-content');
    
    if (classes.length === 0) {
        container.innerHTML = '<p class="no-classes">No classes unlocked yet. Perform actions to unlock new classes!</p>';
        return;
    }
    
    container.innerHTML = classes.map(pc => {
        const c = pc.class_data;
        const rarityClass = `rarity-${c.rarity.toLowerCase()}`;
        
        return `
            <div class="class-card">
                <h4>
                    ${c.name}
                    <span class="class-rarity ${rarityClass}">${c.rarity}</span>
                </h4>
                <div class="class-description">${c.description}</div>
                <div class="class-stats">
                    ${Object.entries(c.base_stats).map(([stat, value]) => 
                        `<div class="class-stat"><strong>${stat}:</strong> ${value}</div>`
                    ).join('')}
                </div>
                <div class="class-skills">
                    <strong>Skills:</strong>
                    ${c.skills.map(skill => 
                        `<div class="skill-item">
                            <span class="skill-name">${skill.name}</span> (${skill.type}) - ${skill.effect}
                        </div>`
                    ).join('')}
                </div>
            </div>
        `;
    }).join('');
}

// Add message to chat
function addMessage(type, content) {
    const container = document.getElementById('chat-container');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}`;
    messageDiv.innerHTML = `<div class="message-content">${content}</div>`;
    container.appendChild(messageDiv);
    container.scrollTop = container.scrollHeight;
}

// Utility: delay
function delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Initialize on load
window.addEventListener('load', () => {
    initGame();
    // Initial stats update after a short delay
    setTimeout(() => {
        updateStats();
    }, 1000);
    // Periodic stats update (less frequent to avoid spam)
    setInterval(updateStats, 10000); // Update every 10 seconds
});

