tinymce.init({
    selector: 'textarea.tinymce-editor',
    menubar: false,
    plugins: [
        'advlist autolink lists link image charmap print preview anchor',
        'searchreplace visualblocks codesample fullscreen',
        'insertdatetime media table paste help wordcount'
    ],
    toolbar: 'undo redo | image | formatselect | ' +
    'bold italic backcolor codesample superscript subscript | alignleft aligncenter ' +
    'alignright alignjustify | bullist numlist outdent indent | ' +
    'removeformat | help',

    images_upload_url: '/upload_image',
    paste_data_images: true,
    relative_urls: false,

    content_style: "@import url('https://fonts.googleapis.com/css2?family=Inter&display=swap'); \
                    body { font-family: Inter; font-size: 14px; }",

});
