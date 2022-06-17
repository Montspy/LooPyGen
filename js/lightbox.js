// Open the Modal
function openModal(id) {
    document.getElementById(id).style.display = "flex";
    setTimeout(updateProgressModal, 1000, id);
}

const updateProgressModal = async (modalId) => {
    if (updateProgressModal.counter === undefined) {
        updateProgressModal.counter = 0;
    }
    updateProgressModal.counter++;

    // Stop update if modal is hidden
    if (document.getElementById(modalId).style.display === 'none') {
        return;
    }

    const progress = await readProgress();
    if (progress !== null && progress.completed !== undefined && progress.total !== undefined) {
        const progressId = `${modalId}-progress`;
        const spinnerId = `${progressId}--spinner`;
        document.getElementById(progressId).innerHTML = `Progress: ${progress.completed}/${progress.total}`
        const spinner = updateProgressModal.counter % 3 + 1;
        document.getElementById(spinnerId).innerHTML = ''.padEnd(spinner, '.').padEnd(3, '\u00A0')

        // Stop update if task completed
        if(progress.completed === progress.total) {
            return;
        }
    }

    setTimeout(updateProgressModal, 1000, modalId);
}

const readProgress = async () => {
    try {
        var response = await fetch('http://localhost:8080/php/progress.json');
    } catch (error) {
        console.log('updateProgressModal: ', error);
        return null;
    }

    try {
        var progress = await response.json();
        return progress;
    } catch (error) {
        console.log('updateProgressModal: ', error);
        return null;
    }

    return null;
}

// Close the Modal
function closeModal(id) {
    document.getElementById(id).style.display = "none";
}
