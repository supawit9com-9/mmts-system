document.addEventListener('DOMContentLoaded', () => {
    
    // ทำ Smooth Scroll เวลาคลิกเมนู
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            document.querySelector(this.getAttribute('href')).scrollIntoView({
                behavior: 'smooth'
            });
        });
    });

    // TODO: เพิ่มฟังก์ชัน Hamburger Menu สำหรับมือถือในอนาคต
    console.log("Website Loaded Ready for Siam Thai Steel");
});