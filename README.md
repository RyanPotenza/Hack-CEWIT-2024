# Hack-CEWIT-2024
# EV Route Planner

This project is a web application developed during the 2024 Hack@CEWIT Hackathon by the Center of Excellence in Wireless and Information Technology (CEWIT) at Stony Brook University. The EV Route Planner allows users to plan electric vehicle (EV) routes, visualize them on a map, and calculate carbon emissions for different transport modes.

## How to Use

To use this tool, you will need a GCP API Key. Follow these steps to set up and run the application locally:

1. **Obtain a GCP API Key**: Obtain a Google Cloud Platform (GCP) API Key from the Google Cloud Console.

2. **Create APIKey.txt**: Create a file named "APIKey.txt" in the base directory of the repository and paste the raw API key on the first line.

3. **Clone the Repository**: Clone this repository to your local machine using Git:

    ```bash
    git clone https://github.com/your-username/ev-route-planner.git
    ```

4. **Navigate to the Directory**: Navigate to the directory of the cloned repository:

    ```bash
    cd ev-route-planner
    ```

5. **Run the Flask Server**: Start the Flask server by running the "flaskServer.py" file. Ensure that the terminal remains open while the server is running:

    ```bash
    python flaskServer.py
    ```

6. **Access the Web App**: Open a web browser and go to [http://localhost:5000/](http://localhost:5000/) to access the home page of the EV Route Planner.

Follow the on-screen instructions to plan EV routes, select transport modes, and visualize them on the map. Ensure that the Flask server is running to access the service at any point.

For any further assistance or inquiries, please contact the project team.
