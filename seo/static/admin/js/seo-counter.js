(function initSEOcounter() {
    if (typeof django === "undefined" || typeof django.jQuery === "undefined") {
        return setTimeout(initSEOcounter, 50);
    }

    (function($) {
        $(function() {

            // --- Character Counter Logic (already working) ---

            function updateCounter(field, counterSpan, maxLength) {
                var length = field.val().length;
                var remaining = maxLength - length;
                var color = remaining < 0 ? 'red' : (remaining < 20 ? 'orange' : 'green');

                counterSpan.text(length + '/' + maxLength + ' characters')
                           .css('color', color);
            }

            // Add counters to inputs
            $('.field-meta_title input').after('<span class="char-counter"></span>');
            $('.field-meta_description input').after('<span class="char-counter"></span>');

            var titleField = $('.field-meta_title input');
            var titleCounter = $('.field-meta_title .char-counter');
            var descField = $('.field-meta_description input');
            var descCounter = $('.field-meta_description .char-counter');

            // --- LIVE SEO PREVIEW UPDATE ---

            function truncate(text, max) {
                return text.length > max ? text.substring(0, max) + "..." : text;
            }

            function updateSEOPreview() {
                var title = titleField.val();
                var desc = descField.val();

                $('#seo-preview-title').text(truncate(title, 60));
                $('#seo-preview-description').text(truncate(desc, 160));

                // Update counters under preview
                $('#seo-title-count')
                    .text('Title: ' + title.length + '/60 chars')
                    .css('color', title.length > 60 ? 'red' : 'green');

                $('#seo-desc-count')
                    .text('Description: ' + desc.length + '/160 chars')
                    .css('color', desc.length > 160 ? 'red' : 'green');
            }

            titleField.on('input', function() {
                updateCounter($(this), titleCounter, 60);
                updateSEOPreview();
            }).trigger('input');

            descField.on('input', function() {
                updateCounter($(this), descCounter, 160);
                updateSEOPreview();
            }).trigger('input');

        });
    })(django.jQuery);
})();
