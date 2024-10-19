const pricingData = {
    ayla: [
        { label: "Mentorship", price: "$150/month" },
        { label: "Intro Session", price: "$39" },
        { label: "CV Review", price: "$69" },
        { label: "Launch Plan", price: "$129" }
    ],
    francois: [
        { label: "Mentorship", price: "$99/month" },
        { label: "Intro Session", price: "$39" },
        { label: "CV Review", price: "$69" },
        { label: "Launch Plan", price: "$129" }
    ],
    annie: [
        { label: "Mentorship", price: "$50/month" },
        { label: "Intro Session", price: "$39" },
        { label: "Portfolio Review", price: "$69" },
        { label: "Expert Session", price: "$140" }
    ]
};

function addPriceTags(mentor, pricing) {
    const card = document.querySelector(`.card.${mentor}`);
    pricing.forEach(item => {
        const priceTag = document.createElement('div');
        priceTag.classList.add('oval-price');
        priceTag.textContent = `${item.label} ${item.price}`;
        card.appendChild(priceTag);
    });
}

addPriceTags('ayla', pricingData.ayla);
addPriceTags('francois', pricingData.francois);
addPriceTags('annie', pricingData.annie);
