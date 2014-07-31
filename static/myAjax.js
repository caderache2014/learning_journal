$(document).ready(function () {
    $('.add_entry').on('submit', function(addEntry){
        addEntry.preventDefault();
        $.ajax('/add', {
            type: 'POST',
            data: $('form').serialize(),
            success: function(entryData) {
                alert(entryData)
                $('.newEntry').html(entryData);
                $('.add_entry').remove();
            }
        });
    });
});

$(document).ready(function () {
    $('.edit').on('submit', function(changeEntry){
        changeEntry.preventDefault();
        $.ajax('/update_entry', {
            type: 'POST',
            data: $('form').serialize(),
            success: function(entryData) {
                alert(entryData)
                $('.newEntry').html(entryData);
                $('.edit').remove();
            }
        });
    });
});