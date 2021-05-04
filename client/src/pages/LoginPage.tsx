import React from 'react';
import {
    Box,
    Button,
    Heading,
    SimpleGrid,
    Text,
    useColorModeValue,
    VisuallyHidden,
    Link
} from '@chakra-ui/react'
import { Link as RouterLink } from 'react-router-dom';
import { FaFacebook, FaGithub, FaGoogle } from 'react-icons/fa'
import { Card } from '../components/Card';
import { DividerWithText } from '../components/DividerWithText'
import { LoginForm } from '../components/AuthForm/LoginForm'

interface LoginPageProps {

}

const LoginPage: React.FC<LoginPageProps> = () => {
    return (
        <Box
        bg={useColorModeValue('gray.50', 'inherit')}
        minH="100vh"
        py="12"
        px={{ base: '4', lg: '8' }}
      >
        <Box maxW="md" mx="auto">
          <Box>Logo Placeholder</Box>
          <Heading textAlign="center" size="xl" fontWeight="extrabold">
            Sign in to your account
          </Heading>
          <Text mt="4" mb="8" align="center" maxW="md" fontWeight="medium">
            <Text as="span">Don't have an account? </Text>
            <Link
                color={useColorModeValue('blue.500', 'blue.200')}
                _hover={{ color: useColorModeValue('blue.600', 'blue.300') }}
                display={{ base: 'block', sm: 'inline' }}
                as={RouterLink}
                to="/signup">
                    Sign up
            </Link>
          </Text>
          <Card>
            <LoginForm />
            <DividerWithText mt="6">or continue with</DividerWithText>
            <SimpleGrid mt="6" columns={3} spacing="3">
              <Button color="currentColor" variant="outline">
                <VisuallyHidden>Login with Facebook</VisuallyHidden>
                <FaFacebook />
              </Button>
              <Button color="currentColor" variant="outline">
                <VisuallyHidden>Login with Google</VisuallyHidden>
                <FaGoogle />
              </Button>
              <Button color="currentColor" variant="outline">
                <VisuallyHidden>Login with Github</VisuallyHidden>
                <FaGithub />
              </Button>
            </SimpleGrid>
          </Card>
        </Box>
      </Box>

    );
}

export default LoginPage;