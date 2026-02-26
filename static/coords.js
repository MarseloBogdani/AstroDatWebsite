document.addEventListener('keydown', function (e) {
    if (!e.target.classList.contains('coord-mask') && !e.target.classList.contains('dec-mask')) return;

    if (e.key === 'Backspace') {
        const input = e.target;
        const start = input.selectionStart;
        const end = input.selectionEnd;

        if (start === end && start > 0) {
            const value = input.value;
            const charBefore = value.substring(start - 1, start);
            
            const jumps = {
                ' ': 4,  
                's': 3,  
                '"': 3,  
                'h': 3,  
                'm': 3, 
                '°': 3,  
                "'": 3   
            };

            if (jumps[charBefore]) {
                e.preventDefault();
                const jumpSize = jumps[charBefore];
                
                input.value = value.substring(0, start - jumpSize) + value.substring(end);
                const newPos = Math.max(0, start - jumpSize);
                input.setSelectionRange(newPos, newPos);
                
                input.dispatchEvent(new Event('input'));
            }
        }
    }
});

document.addEventListener('input', function (e) {
    const input = e.target;
    if (input.classList.contains('coord-mask')) {
        handleRA(input);
    } else if (input.classList.contains('dec-mask')) {
        handleDec(input);
    }
});

function handleRA(input) {
    let digits = input.value.replace(/\D/g, ''); 
    let formatted = '';
    if (digits.length > 0) formatted += digits.substring(0, 2) + 'h ';
    if (digits.length > 2) {
        let mins = digits.substring(2, 4);
        if (parseInt(mins) > 59) mins = '59';
        formatted += mins + 'm ';
    }
    if (digits.length > 4) {
        let secs = digits.substring(4, 6);
        if (parseInt(secs) > 59) secs = '59';
        formatted += secs + 's';
    }
    input.value = formatted.trim();
}

function handleDec(input) {
    let sign = '';
    if (input.value.startsWith('-')) sign = '-';
    else if (input.value.startsWith('+')) sign = '+';
    
    let digits = input.value.replace(/\D/g, '');
    let formatted = sign;

    if (digits.length > 0) {
        let degs = digits.substring(0, 2);
        if (parseInt(degs) > 90) degs = '90';
        formatted += degs + '° ';
        
        let isMax = parseInt(degs) === 90;

        if (digits.length > 2) {
            let mins = isMax ? '00' : digits.substring(2, 4);
            if (parseInt(mins) > 59) mins = '59';
            formatted += mins + "' ";
        }
        if (digits.length > 4) {
            let secs = isMax ? '00' : digits.substring(4, 6);
            if (parseInt(secs) > 59) secs = '59';
            formatted += secs + '"';
        }
    }
    input.value = formatted.trim();
}
