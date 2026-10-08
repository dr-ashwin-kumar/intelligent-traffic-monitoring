const multer = require('multer');
const path = require('path');
const crypto = require('crypto');

const storage = multer.diskStorage({

    destination: (req, file, cb) => {

        cb(null, path.join(__dirname, '../uploads'));

    },

    filename: (req, file, cb) => {

        const uniqueName = crypto.randomUUID() + path.extname(file.originalname);

        cb(null, uniqueName);

    }

});

const upload = multer({

    storage,

    limits: {

        fileSize: 25 * 1024 * 1024

    }

});

module.exports = upload;